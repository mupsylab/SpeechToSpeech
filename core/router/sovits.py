import os
import sys
import json
import fastapi
from io import BytesIO
from typing import Generator
from fastapi.responses import JSONResponse, StreamingResponse

sys.path.append("./model/GPT_SoVITS")
from model.GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
from model.GPT_SoVITS.TTS_infer_pack.text_segmentation_method import get_method_names as get_cut_method_names

from ..utils.cache import cache
from ..utils.audio import wave_header_chunk, pack_audio

router = fastapi.APIRouter(prefix="/api")

tts_config = TTS_Config(os.getenv("GPT_SoVITS", "model_pretrained/GPT_SoVITS/tts_infer.yaml"))
tts_pipeline = TTS(tts_config)
tts_pipeline.set_prompt_cache(
    os.getenv("PROMPT_AUDIO", "model_pretrained/GPT_SoVITS/ssy.wav"),
    os.getenv("PROMPT_TEXT", "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。"),
    "zh"
)

def check_params(req:dict):
    text:str = req.get("text", "")
    text_lang:str = req.get("text_lang", "")
    ref_audio_path:str = req.get("ref_audio_path", "")
    streaming_mode:bool = req.get("streaming_mode", False)
    media_type:str = req.get("media_type", "wav")
    prompt_lang:str = req.get("prompt_lang", "")
    text_split_method:str = req.get("text_split_method", "cut5")

    # if ref_audio_path in [None, ""]:
        # return JSONResponse(status_code=400, content={"message": "ref_audio_path is required"})
    if text in [None, ""]:
        return JSONResponse(status_code=400, content={"message": "text is required"})
    if (text_lang in [None, ""]) :
        return JSONResponse(status_code=400, content={"message": "text_lang is required"})
    elif text_lang.lower() not in tts_config.languages:
        return JSONResponse(status_code=400, content={"message": f"text_lang: {text_lang} is not supported in version {tts_config.version}"})
    # if (prompt_lang in [None, ""]) :
        # return JSONResponse(status_code=400, content={"message": "prompt_lang is required"})
    # elif prompt_lang.lower() not in tts_config.languages:
        # return JSONResponse(status_code=400, content={"message": f"prompt_lang: {prompt_lang} is not supported in version {tts_config.version}"})
    if media_type not in ["wav", "raw", "ogg", "aac"]:
        return JSONResponse(status_code=400, content={"message": f"media_type: {media_type} is not supported"})
    elif media_type == "ogg" and  not streaming_mode:
        return JSONResponse(status_code=400, content={"message": "ogg format is not supported in non-streaming mode"})
    
    if text_split_method not in get_cut_method_names():
        return JSONResponse(status_code=400, content={"message": f"text_split_method:{text_split_method} is not supported"})

    return None
async def tts_handle(req:dict):
    streaming_mode = req.get("streaming_mode", False)
    return_fragment = req.get("return_fragment", False)
    media_type = req.get("media_type", "wav")

    check_res = check_params(req)
    if check_res is not None:
        return check_res

    if streaming_mode or return_fragment:
        req["return_fragment"] = True
    
    try:
        tts_generator=tts_pipeline.run(req)
        
        if streaming_mode:
            def streaming_generator(tts_generator:Generator, media_type:str):
                if media_type == "wav":
                    yield wave_header_chunk()
                    media_type = "raw"
                for sr, chunk in tts_generator:
                    yield pack_audio(BytesIO(), chunk, sr, media_type).getvalue()
            # _media_type = f"audio/{media_type}" if not (streaming_mode and media_type in ["wav", "raw"]) else f"audio/x-{media_type}"
            return StreamingResponse(streaming_generator(tts_generator, media_type, ), media_type=f"audio/{media_type}")
    
        else:
            sr, audio_data = next(tts_generator)
            audio_data = pack_audio(BytesIO(), audio_data, sr, media_type).getvalue()
            return fastapi.Response(audio_data, media_type=f"audio/{media_type}")
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"tts failed", "Exception": str(e)})


from .interface import TTS_Request
@router.post("/tts/vits")
async def gpt_sovits(request: TTS_Request):
    name = cache.save(request.model_dump_json())
    return fastapi.responses.JSONResponse(status_code=200,
                                          content={"id": name})

@router.get("/tts/vits")
async def generate_audio(id: str):
    req = json.loads(cache.load(id))
    return await tts_handle(req)


