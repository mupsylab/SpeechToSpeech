import sys
sys.path.append("./model/GPT_SoVITS")

import json
import fastapi

from ..model.sovits import TTS_Request, tts_handle
from ..utils.cache import cache

router = fastapi.APIRouter(prefix="/api")

@router.post("/tts/vits")
async def gpt_sovits(request: TTS_Request):
    name = cache.save(request.model_dump_json())
    return fastapi.responses.JSONResponse(status_code=200,
                                          content={"id": name})

@router.get("/tts/vits")
async def generate_audio(id: str):
    config: dict = json.loads(cache.load(id))
    resp = await tts_handle(config)
    if isinstance(resp, bytes):
        return fastapi.Response(resp, media_type=f"audio/{config.get('media_type', 'wav')}")
    else:
        return fastapi.responses.StreamingResponse(resp, media_type=f"audio/{config.get('media_type', 'wav')}")

