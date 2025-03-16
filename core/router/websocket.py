import base64
import fastapi
import asyncio
import numpy as np
from pydantic import BaseModel
from typing import Literal
from logging import getLogger
logger = getLogger(__name__)

from model.denoise import denoise
from model.sensor import vad_array, asr_array
from . import ChatManager, session_manager, chat, stream_io

router = fastapi.APIRouter()
@router.websocket("/ws/{session_id}")
async def ws(websocket: fastapi.WebSocket, session_id: str):
    await websocket.accept()
    session = session_manager.get(session_id)
    if session is None:
        await websocket.close()
    else:
        ws = WebsocketClient(websocket)
        ws.session_id = session_id
        session["ws"] = ws
        session["chat"] = ChatManager()
        await ws.run()

@router.get("/api/tts")
async def tts(request: fastapi.Request):
    session_id = request.cookies.get("session")
    session = session_manager.get(session_id)
    return fastapi.responses.StreamingResponse(stream_io(generate_msg(session)), media_type="audio/wav")


@router.get("/api/history")
async def history(request: fastapi.Request):
    session_id = request.cookies.get("session")
    session = session_manager.get(session_id)
    if "chat" not in session:
        return fastapi.responses.JSONResponse({
            "history": []
        })
    cm: ChatManager = session["chat"]
    return fastapi.responses.JSONResponse({
        "history": [item.model_dump() for item in cm.cache]
    })


def generate_msg(session: dict[str, any]):
    cm: ChatManager = session["chat"]
    ws: WebsocketClient = session["ws"]
    if len(cm.cache) and cm.cache[-1].role == "assistant":
        yield cm.cache[-1].content
    else:
        for resp in chat(cm.get_llm_message()):
            if resp.type == "char":
                # 流式输出llm的响应
                asyncio.run(ws.ws.send_text("stream:llm:%s" % resp.content))
            if resp.type == "sentence":
                logger.debug("start generate llm sentence: %s" % resp.content)
                if resp.content.strip():
                    # 确保有真实的内容                
                    yield resp.content
        cm.add_chat(resp.content, "assistant")


class WebsocketMessage(BaseModel):
    action: Literal["init", "record", "finish"]
    param: dict[str, str | int] = {}


class WebsocketClient:
    def __init__(self, ws: fastapi.WebSocket) -> None:
        self.rest_time = 400 # 讲话时，最长允许的停顿时间, 单位ms
        self.min_audio_frame_len = 25 * 0.001 # 最小音频帧应该保证25毫秒
        
        self.ws = ws
        self.session_id = None # session，便于相互索引
        self.sampleRate: int = 0
        self.audioBuffer: np.ndarray = np.array([], dtype=np.float32)

        self._task_queue = asyncio.Queue()  # 任务队列
        self._running = True

    def _tran_ms_to_audioframe(self, ms: int):
        return int(ms / 1000 * self.sampleRate)

    def _load_audio_buffer(self, blob):
        array = np.frombuffer(blob, dtype=np.int16).astype(np.float32)
        array = denoise(array, self.sampleRate)
        if array.std() > 300:
            # 如果音频片段达到了要求
            self.audioBuffer = np.concatenate([self.audioBuffer, array], dtype = np.float32, axis = 0)
            return True
        else:
            # 插入空白音频片段，避免问题
            self.audioBuffer = np.concatenate([self.audioBuffer, np.zeros(array.shape[0], dtype=np.float32)], dtype = np.float32, axis = 0)
            return False

    async def asr(self, item: list[int]):
        [startPos, stopPos] = [self._tran_ms_to_audioframe(item[0]), self._tran_ms_to_audioframe(item[1])]
        audioBuffer = self.audioBuffer[startPos:stopPos]

        audioPad = int(self.sampleRate * self.min_audio_frame_len) - audioBuffer.shape[0]
        if audioPad > 0:
            audioBuffer = np.concatenate([audioBuffer, np.zeros(audioPad, dtype=np.float32)], axis = 0, dtype=np.float32)

        asr = asr_array(audioBuffer, sampleRate=self.sampleRate, lang="zh")
        logger.debug("asr result: %s" % (asr.clean_text))
        if len(asr.clean_text):
            cm: ChatManager = session_manager.get(self.session_id)["chat"]
            cm.add_chat(asr.clean_text, "user")
            await self.ws.send_text("stream:asr:%s" % asr.text)
            return True
        return False

    async def valid(self):
        # 验证音频是否存在声音，且停止讲话
        array = self.audioBuffer
        audio_len = (array.shape[0] / self.sampleRate) * 1000 # ms

        [items, param] = vad_array(array, sampleRate = self.sampleRate)
        logger.debug(items)

        if not len(items):
            # 没有有效的音频, 清空缓存
            self.audioBuffer = np.array([], dtype=np.float32)
            return False

        await self.ws.send_text("tts:stop")
        if len(items) > 1:
            # 超过一段的语音内容，识别前几段
            for item in items[:-1]:
                await self.asr(item)
        if audio_len - items[-1][1] > self.rest_time:
            # 超过指定时长没有新的语音输入，意味着结束讲话
            r = await self.asr(items[-1])
            if r:
                await self.ws.send_text("tts:start")
            self.audioBuffer = np.array([], dtype=np.float32)
        elif len(items) > 1:
            # 删除前几段
            self.audioBuffer = self.audioBuffer[self._tran_ms_to_audioframe(items[-1][0]):]

    async def action(self, wm: WebsocketMessage):
        if wm.action == "init":
            self.sampleRate = int(wm.param["sampleRate"])
        elif self.sampleRate <= 0:
            # 还未初始化
            return
        elif wm.action == "record":
            self._load_audio_buffer(base64.b64decode(wm.param["audio"]))
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
                logger.error(f"Error processing action: {e}", stack_info=True, exc_info=1)
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

