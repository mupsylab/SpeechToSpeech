from enum import Enum
from typing_extensions import Annotated
from typing import Generator

import os, re, sys

now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append("%s/model/GPT_SoVITS" % (now_dir))

import uuid, json
from io import BytesIO
from funasr import AutoModel
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from fastapi.responses import StreamingResponse, JSONResponse
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from TTS_infer_pack.TTS import TTS, TTS_Config
from TTS_infer_pack.text_segmentation_method import get_method_names as get_cut_method_names

from interface import Language, TTS_Request
from utils import pack_audio, wave_header_chunk

if not os.path.exists("TEMP"):
    os.mkdir("TEMP")

sv_model = AutoModel(
    model=os.environ.get("SENSE_MODEL"),
    trust_remote_code=True,
    remote_code="./model/SensorVoice/model.py",
    vad_model=os.environ.get("VAD_MODEL"),
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
)
tts_config = TTS_Config(os.environ.get("GPT_SoVITS"))
tts_pipeline = TTS(tts_config)
tts_pipeline.set_prompt_cache(
    os.environ.get("PROMPT_AUDIO"),
    os.environ.get("PROMPT_TEXT"),
    "zh"
)

cut_method_names = get_cut_method_names()
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
    
    if text_split_method not in cut_method_names:
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
            return Response(audio_data, media_type=f"audio/{media_type}")
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"tts failed", "Exception": str(e)})

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境中使用
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/asr")
async def sensor_voice_asr(file: UploadFile = File(...),
                           lang: Annotated[Language, Form(description="language of audio content")] = "auto"):
    if lang == "":
        lang = "auto"
    try:
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type")
        unique_filename = str(uuid.uuid4()) + ".mp3"
        audio_file_path = os.path.join("TEMP", unique_filename)
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(await file.read())

        res = sv_model.generate(
            input=audio_file_path,
            cache={},
            language=lang,
            use_itn=True,
            batch_size=1,
            merge_vad=True,
            merge_length_s=15,
        )
        os.unlink(audio_file_path)
        if len(res) == 0:
            return { "result": [] }

        print(res)
        text = res[0]["text"]
        return {
            "result": {
                "raw_text": text,
                "text": rich_transcription_postprocess(text),
                "clean_text": re.sub(r"<\|.*\|>", "", text, 0, re.MULTILINE)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts")
async def tts_general(file_id: str):
    with open("TEMP/{}.json".format(file_id), "r") as f:
        req = json.loads(f.read())
    os.unlink("TEMP/{}.json".format(file_id))
    return await tts_handle(req)

@app.post("/api/tts")
async def tts_post_endpoint(request: TTS_Request):
    req = request.dict()
    file_id = str(uuid.uuid4())
    with open("TEMP/{}.json".format(file_id), "w") as f:
        f.write(json.dumps(req, ensure_ascii=False))
    return JSONResponse(status_code=200, content = {
        "file_id": file_id
    })

