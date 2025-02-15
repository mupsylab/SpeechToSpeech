from __future__ import annotations
import sys
import fastapi
import torch, torchaudio
import numpy as np
from typing import Generator
from io import BytesIO

sys.path.append("./model")
from model.cosyvoice.cli.cosyvoice import CosyVoice2
from model.cosyvoice.utils.file_utils import load_wav

from ..utils.audio import wave_header_chunk, pack_audio

router = fastapi.APIRouter(prefix = "/api")

@router.post("/tts/cosy")
async def speech_zero_shot(tts_text: str = fastapi.Form(),
                           stream: bool = fastapi.Form(default = False)):
    return fastapi.responses.StreamingResponse(
        inferce_zero_shot(tts_text, stream),
        media_type = "audio/wav"
    ) if stream else fastapi.Response(
        inferce_zero_shot(tts_text, stream),
        media_type = "audio/wav"
    )

def load():
    return CosyVoice2('model_pretrained/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=False)
cosyvoice: CosyVoice2 = load()
def inferce_zero_shot(tts_text: str | Generator[str], stream: bool = False):
    model_output = cosyvoice.inference_sft(
        tts_text,
        spk_id="中文女",
        stream=stream, text_frontend=False
    )
    if stream:
        yield wave_header_chunk(sample_rate = cosyvoice.sample_rate)
        for item in model_output:
            yield pack_audio(
                BytesIO(),
                (item["tts_speech"] * (2 ** 15)).numpy().astype(np.int16),
                cosyvoice.sample_rate,
                "raw"
            ).getvalue()
    else:
        for item in model_output:
            audio = BytesIO()
            torchaudio.save(audio, item["tts_speech"], cosyvoice.sample_rate, format = "wav")
            blob = audio.getvalue()
            audio.close()
            return blob



