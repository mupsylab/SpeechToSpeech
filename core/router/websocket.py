import base64
import fastapi
import threading
import numpy as np
from pydantic import BaseModel
from typing import Literal

from ..utils.audio import wave_header_chunk
from ..model.sensor import vad_array, asr_array

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
        
    def audio_array(self):
        array = np.frombuffer(self.chunk, dtype=np.int16).astype(np.float32)
        return array

    def valid(self):
        # 验证音频是否存在声音，且停止讲话
        array = self.audio_array()
        audio_len = (array.shape[0] / self.sampleRate) * 1000 # ms
        if audio_len < 500:
            return False
        [items, param] = vad_array(array, sampleRate = self.sampleRate)
        if not len(items[0]["value"]):
            # 没有有效的音频, 清空缓存
            self.chunk = b""
            return False
        if audio_len - items[0]["value"][-1][1] > 200:
            # 超过200ms没有新的语音输入，意味着结束讲话
            return True
        return False

    def action(self, wm: WebsocketMessage):
        if wm.action == "init":
            self.sampleRate = int(wm.param["sampleRate"])
        elif wm.action == "record":
            blob = base64.b64decode(wm.param["audio"])
            self.chunk += blob
            if self.valid():
                # 说话完成
                resp = asr_array(self.audio_array(), self.sampleRate)
                print(resp.clean_text)
                self.chunk = b""
        elif wm.action == "finish":
            with open("model_pretrained/a.wav", "wb") as f:
                f.write(self.chunk)
            with open("model_pretrained/b.wav", "wb") as f:
                f.write(wave_header_chunk(sample_rate = self.sampleRate))
                f.write(self.chunk)


    async def run(self):
        while True:
            data = WebsocketMessage.model_validate(await self.ws.receive_json())
            self.action(data)


