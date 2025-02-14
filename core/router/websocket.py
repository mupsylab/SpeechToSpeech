from  __future__ import annotations
import json
import fastapi
from typing import Annotated, List
router = fastapi.APIRouter()

from .interview import put_llm, generate_msg
from .sensor import sensor_voice_asr
@router.post("/api/asr")
async def asr(files: Annotated[List[bytes], fastapi.File(description="wav or mp3 audios in 16KHz")],
              keys: Annotated[str, fastapi.Form(description="name of each audio joined with comma")],
              cid: Annotated[int, fastapi.Form()] = None,
              lang: Annotated[str, fastapi.Form(description="language of audio content")] = "auto"):
    resp = await sensor_voice_asr(files, keys, lang)
    if cid is None:
        return resp
    m = json.loads(resp.body)["result"]["text"]
    if m is not None and len(m):
        await put_llm(m, cid)
    return fastapi.Response(str(generate_snowflake_id()))

from .cosy import speech_instruct
@router.get("/api/tts")
async def tts(cid: int):
    return await speech_instruct(generate_msg(cid), 
                                 "用舒缓的语气说", True)

from ..utils.snowflake import generate_snowflake_id
@router.get("/api/id")
async def get_id():
    return fastapi.Response(str(generate_snowflake_id()))
