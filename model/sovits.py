from __future__ import annotations
import os
import sys
from io import BytesIO
from typing import Generator
sys.path.append("./model/GPT_SoVITS")
from logging import getLogger
logger = getLogger(__name__)

from model.GPT_SoVITS.TTS import TTS, TTSRunParam, TTS_Config

from core.utils.audio import wave_header_chunk, pack_audio

def stream_io(tts_text: Generator[str]):
    logger.debug("start generate tts")
    for i1, text in enumerate(tts_text):
        model_output = tts_handle(TTSRunParam(text=text, text_lang="zh", streaming_mode=True))
        for i2, item in enumerate(model_output):
            if i1 != 0 and i2 == 0:
                continue
            logger.debug("generate tts...")
            yield item

tts_config = TTS_Config(os.getenv("GPT_SoVITS", "model_pretrained/GPT_SoVITS/tts_infer.yaml"))
tts_pipeline = TTS(tts_config)
tts_pipeline.set_prompt_cache(
    os.getenv("PROMPT_AUDIO", "model_pretrained/GPT_SoVITS/ssy.wav"),
    os.getenv("PROMPT_TEXT", "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。"),
    "zh"
)

def tts_handle(req: TTSRunParam):
    streaming_mode = req.streaming_mode
    return_fragment = req.return_fragment
    media_type = req.media_type

    if streaming_mode or return_fragment:
        req.return_fragment = True

    try:
        tts_generator=tts_pipeline.run(req)
        
        if streaming_mode:
            def streaming_generator(tts_generator:Generator, media_type:str):
                for sr, chunk in tts_generator:
                    if media_type == "wav":
                        yield wave_header_chunk(sample_rate = sr)
                        media_type = "raw"
                    yield pack_audio(BytesIO(), chunk, sr, media_type).getvalue()
            # _media_type = f"audio/{media_type}" if not (streaming_mode and media_type in ["wav", "raw"]) else f"audio/x-{media_type}"
            return streaming_generator(tts_generator, media_type)

        else:
            sr, audio_data = next(tts_generator)
            audio_data = pack_audio(BytesIO(), audio_data, sr, media_type).getvalue()
            return audio_data
    except Exception as e:
        raise RuntimeError("tts failed")
