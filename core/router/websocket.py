import base64
import fastapi
import asyncio
import numpy as np
from pydantic import BaseModel
from typing import Literal

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
        self.ws = ws
        self.sampleRate: int = 0
        self.chunk: bytes = b""

        self._task_queue = asyncio.Queue()  # 任务队列
        self._running = True

    def audio_array(self):
        array = np.frombuffer(self.chunk, dtype=np.int16).astype(np.float32)
        return array

    async def valid(self):
        # 验证音频是否存在声音，且停止讲话
        array = self.audio_array()
        audio_len = (array.shape[0] / self.sampleRate) * 1000 # ms
        if audio_len < 500:
            return False
        [items, param] = vad_array(array, sampleRate = self.sampleRate)
        if not len(items[0]["value"]) or \
            (len(items[0]["value"]) == 1 and items[0]["value"][0][0] == 0):
            # 没有有效的音频, 清空缓存
            self.chunk = b""
            return False
        await self.ws.send_text("tts:stop")
        if audio_len - items[0]["value"][-1][1] > 200:
            # 超过200ms没有新的语音输入，意味着结束讲话
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
            self.chunk += blob
            if await self.valid():
                # 说话完成
                resp = asr_array(self.audio_array(), self.sampleRate)
                self.chunk = b""
                if len(resp.clean_text):
                    # 有字，代表识别正确
                    cm.add_chat(resp.clean_text, "user")
                    await self.ws.send_text("tts:start")


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
                print(f"Error processing action: {e}")
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
            print("Client disconnected")
        finally:
            # 清理资源
            self._running = False
            await self._task_queue.put(None)  # 发送终止信号
            await worker_task  # 等待 worker 完成

