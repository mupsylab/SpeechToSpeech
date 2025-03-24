from __future__ import annotations
import os
import sys
sys.path.append("./model/GPT_SoVITS")
from logging import getLogger
logger = getLogger(__name__)

from model.GPT_SoVITS.TTS import TTS, TTSRunParam, TTS_Config

def stream_io(tts_text: str):
    model_output = tts_handle(TTSRunParam(text=tts_text, text_lang="zh", streaming_mode=True))
    for item in model_output:
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

    if streaming_mode or return_fragment:
        req.return_fragment = True

    try:
        tts_generator=tts_pipeline.run(req)
        
        if streaming_mode:
            for sr, chunk in tts_generator:
                yield chunk, sr

        else:
            sr, audio_data = next(tts_generator)
            yield audio_data, sr
    except Exception as e:
        raise RuntimeError("tts failed")
