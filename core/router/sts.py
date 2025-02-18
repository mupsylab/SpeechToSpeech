from  __future__ import annotations
import json
import fastapi
from typing import Annotated, List
router = fastapi.APIRouter()

"""
LLM聊天管理
"""
from ..llm import ChatManager
from ..llm.chatgpt import chat
cm = ChatManager()
def generate_msg():
    if len(cm.cache) and cm.cache[-1].role == "assistant":
        yield cm.cache[-1].content
    else:
        for resp in chat(cm.get_llm_message()):
            if resp.type == "sentence":
                yield resp.content
        cm.add_chat(resp.content, "assistant")

from ..model.sensor import asr as sensor
@router.post("/api/asr")
async def asr(files: Annotated[List[bytes], fastapi.File(description="wav or mp3 audios in 16KHz")],
              keys: Annotated[str, fastapi.Form(description="name of each audio joined with comma")],
              lang: Annotated[str, fastapi.Form(description="language of audio content")] = "auto"):
    resp = sensor(files[0], lang)
    if len(resp.text):
        cm.add_chat(resp.text, "user")
    return fastapi.responses.JSONResponse({
        "history": list(map(lambda x: x.model_dump(), cm.cache))
    })

from ..model.cosy import stream_io
@router.get("/api/tts")
async def tts():
    return fastapi.responses.StreamingResponse(stream_io(generate_msg()), media_type="audio/wav")
