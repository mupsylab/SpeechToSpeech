import fastapi
from fastapi.responses import JSONResponse
from typing import List
from typing_extensions import Annotated

from ..model.sensor import asr, asr_adv, Language
from ..utils.cache import cache

router = fastapi.APIRouter(prefix="/api")

@router.post("/asr/v1")
async def sensor_voice_asr(files: Annotated[List[fastapi.UploadFile], fastapi.File(description="wav or mp3 audios in 16KHz")], 
                           lang: Annotated[Language, fastapi.Form(description="language of audio content")] = "auto"):
    file = files[0]
    blob = await file.read()
    res = asr(blob, lang)
    return JSONResponse({
        "result": res.model_dump()
    })


@router.post("/asr/v2")
async def sensor_voice_asr2(files: Annotated[List[fastapi.UploadFile], fastapi.File(description="wav or mp3 audios in 16KHz")],
                            lang: Annotated[Language, fastapi.Form(description="language of audio content")] = "auto"):
    file = files[0]
    blob = await file.read()
    file_path = cache.get_path(cache.save(blob))

    res = asr_adv(file_path, lang)
    
    return JSONResponse({
        "result": res.model_dump()
    })
