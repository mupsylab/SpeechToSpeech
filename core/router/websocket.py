import base64
import fastapi
import asyncio
import numpy as np
from pydantic import BaseModel
from typing import Literal
import logging
logger = logging.getLogger(__name__)

from ..model.sensor import vad_array, asr_array
from .sts import cm

router = fastapi.APIRouter()
@router.websocket("/ws")
async def ws(websocket: fastapi.WebSocket):
    await websocket.accept()
    await WebsocketClient(websocket).run()


class WebsocketMessage(BaseModel):
    action: Literal["init", "record", "finish"]
    param: dict[str, str | int] = {}


class WebsocketClient:
    def __init__(self, ws: fastapi.WebSocket) -> None:
        self.rest_time = 500 # 讲话时，最长允许的停顿时间, 单位ms
        
        self.ws = ws
        self.sampleRate: int = 0
        self.audioBuffer: np.ndarray = np.array([], dtype=np.float32)

        self._task_queue = asyncio.Queue()  # 任务队列
        self._running = True

    def load_audio_buffer(self, blob):
        array = np.frombuffer(blob, dtype=np.int16).astype(np.float32)
        self.audioBuffer = np.concatenate([self.audioBuffer, array], dtype = np.float32, axis = 0)

    async def valid(self):
        # 验证音频是否存在声音，且停止讲话
        array = self.audioBuffer
        audio_len = (array.shape[0] / self.sampleRate) * 1000 # ms

        [items, param] = vad_array(array, sampleRate = self.sampleRate)
        logger.debug(items)
        
        if not len(items):
            # 没有有效的音频, 清空缓存
            self.audioBuffer: np.ndarray = np.array([], dtype=np.float32)
            return False

        if audio_len - items[-1][1] > self.rest_time:
            # 超过指定时长没有新的语音输入，意味着结束讲话
            asr = asr_array(self.audioBuffer, sampleRate=self.sampleRate, lang="zh")
            self.audioBuffer: np.ndarray = np.array([], dtype=np.float32)
            if len(asr.clean_text):
                cm.add_chat(asr.clean_text, "user")
                logger.debug("asr result: %s" % asr.clean_text)
                await self.ws.send_text("tts:start")
            return True
        return False

    async def action(self, wm: WebsocketMessage):
        if wm.action == "init":
            self.sampleRate = int(wm.param["sampleRate"])
        elif self.sampleRate <= 0:
            # 还未初始化
            return
        elif wm.action == "record":
            blob = base64.b64decode(wm.param["audio"])
            self.load_audio_buffer(blob)
            await self.valid()

    async def _worker(self):
        """后台任务处理 worker"""
        while self._running:
            try:
                # 从队列中获取任务
                wm = await self._task_queue.get()
                if wm is None:
                    break  # 收到终止信号
                await self.action(wm)
            except Exception as e:
                logger.error(f"Error processing action: {e}", stack_info=True)
            finally:
                self._task_queue.task_done()


    async def run(self):
        """启动 WebSocket 客户端"""
        # 启动后台任务处理 worker
        worker_task = asyncio.create_task(self._worker())

        try:
            while True:
                # 接收 WebSocket 消息
                data = await self.ws.receive_json()
                wm = WebsocketMessage.model_validate(data)
                # 将任务放入队列，由后台 worker 处理
                await self._task_queue.put(wm)
        except fastapi.WebSocketDisconnect:
            logger.error(f"Client disconnected")
        finally:
            # 清理资源
            self._running = False
            await self._task_queue.put(None)  # 发送终止信号
            await worker_task  # 等待 worker 完成

