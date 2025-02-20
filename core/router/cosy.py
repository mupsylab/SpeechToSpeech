from __future__ import annotations
import fastapi

from ..model.cosy import stream_io

router = fastapi.APIRouter(prefix = "/api")

@router.post("/tts/cosy")
async def speech_zero_shot(tts_text: str = fastapi.Form()):
    return fastapi.responses.StreamingResponse(
        stream_io([tts_text]),
        media_type = "audio/wav"
    )
