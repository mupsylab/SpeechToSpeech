from  __future__ import annotations
import fastapi
from typing import Annotated, List
from logging import getLogger
logger = getLogger(__name__)

router = fastapi.APIRouter()

from . import cm, generate_msg
from model.cosy import stream_io
@router.get("/api/tts")
async def tts():
    return fastapi.responses.StreamingResponse(stream_io(generate_msg()), media_type="audio/wav")

from model.sensor import asr as sensor
from ..utils.audio import webm2wav
@router.post("/api/asr")
async def asr(files: Annotated[List[bytes], fastapi.File(description="wav or mp3 audios in 16KHz")],
              lang: Annotated[str, fastapi.Form(description="language of audio content")] = "auto"):
    resp = sensor(webm2wav(files[0]), lang)
    if len(resp.text):
        cm.add_chat(resp.text, "user")
    return fastapi.responses.JSONResponse({
        "history": list(map(lambda x: x.model_dump(), cm.cache))
    })

