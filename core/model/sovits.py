import os
import sys
import json
from io import BytesIO
from typing import Generator

sys.path.append("./model/GPT_SoVITS")
from model.GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
from model.GPT_SoVITS.TTS_infer_pack.text_segmentation_method import get_method_names as get_cut_method_names

from ..utils.cache import cache
from ..utils.audio import wave_header_chunk, pack_audio

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
    streaming_mode:bool = req.get("streaming_mode", False)
    media_type:str = req.get("media_type", "wav")
    text_split_method:str = req.get("text_split_method", "cut5")

    if text in [None, ""]:
        raise ValueError("text is required")
    if (text_lang in [None, ""]) :
        raise ValueError("text_lang is required")
    elif text_lang.lower() not in tts_config.languages:
        raise ValueError(f"text_lang: {text_lang} is not supported in version {tts_config.version}")
    if media_type not in ["wav", "raw", "ogg", "aac"]:
        raise ValueError(f"media_type: {media_type} is not supported")
    elif media_type == "ogg" and  not streaming_mode:
        raise ValueError("ogg format is not supported in non-streaming mode")
    if text_split_method not in get_cut_method_names():
        raise ValueError(f"text_split_method:{text_split_method} is not supported")
    return None

async def tts_handle(req:dict):
    streaming_mode = req.get("streaming_mode", False)
    return_fragment = req.get("return_fragment", False)
    media_type = req.get("media_type", "wav")

    check_params(req)

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
            return streaming_generator(tts_generator, media_type)
    
        else:
            sr, audio_data = next(tts_generator)
            audio_data = pack_audio(BytesIO(), audio_data, sr, media_type).getvalue()
            return audio_data
    except Exception as e:
        raise RuntimeError("tts failed")

from pydantic import BaseModel
class TTS_Request(BaseModel):
    text: str = None                           # str.(required) text to be synthesized
    text_lang: str = None                      # str.(required) language of the text to be synthesized
    ref_audio_path: str = None                 # str.(optional) reference audio path
    aux_ref_audio_paths: list = None           # list.(optional) auxiliary reference audio paths for multi-speaker synthesis
    prompt_lang: str = None                    # str.(optional) prompt text for the reference audio
    prompt_text: str = ""                      # str.(optional) language of the prompt text for the reference audio
    top_k:int = 5                              # int. top k sampling
    top_p:float = 1                            # float. top p sampling
    temperature:float = 1                      # float. temperature for sampling
    text_split_method:str = "cut5"             # str. text split method, see text_segmentation_method.py for details.
    batch_size:int = 1                         # int. batch size for inference
    batch_threshold:float = 0.75               # float. threshold for batch splitting.
    split_bucket:bool = True                   # bool. whether to split the batch into multiple buckets.
    speed_factor:float = 1.0                   # float. control the speed of the synthesized audio.
    fragment_interval:float = 0.3              # float. to control the interval of the audio fragment.
    seed:int = -1                              # int. random seed for reproducibility.
    media_type:str = "wav"                     # str. media type of the output audio, support "wav", "raw", "ogg", "aac".
    streaming_mode:bool = False                # bool. whether to return a streaming response.
    parallel_infer:bool = True                 # bool.(optional) whether to use parallel inference.
    repetition_penalty:float = 1.35            # float.(optional) repetition penalty for T2S model.          

