from __future__ import annotations
import sys
import fastapi
import torch, torchaudio
import numpy as np
from io import BytesIO

sys.path.append("./model")
from model.cosyvoice.cli.cosyvoice import CosyVoice2
from model.cosyvoice.utils.file_utils import load_wav

from ..utils.audio import wave_header_chunk, pack_audio

router = fastapi.APIRouter(prefix = "/api")

def load():
    return CosyVoice2('model_pretrained/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=False)
cosyvoice: CosyVoice2 = load()

prompt_speech_16k = load_wav("model_pretrained/GPT_SoVITS/ssy.wav", 16000)
@router.post("/tts/cosy")
async def speech_zero_shot(tts_text: str = fastapi.Form(),
                          stream: bool = fastapi.Form(default = False)):
    model_output: list[dict[str, torch.Tensor]] = cosyvoice.inference_zero_shot(
        tts_text, "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。", prompt_speech_16k, stream = stream
    )
    if not stream:
        for item in model_output:
            audio = BytesIO()
            torchaudio.save(audio, item["tts_speech"], cosyvoice.sample_rate, format = "wav")
            v = audio.getvalue()
            audio.close()
            return fastapi.Response(v, media_type="audio/wav")
    else:
        return fastapi.responses.StreamingResponse(generate_data(model_output), media_type="audio/wav")

def generate_data(model_output: list[dict[str, torch.Tensor]]):
    c = wave_header_chunk(sample_rate=cosyvoice.sample_rate)
    yield c
    for item in model_output:
        b = pack_audio(
            BytesIO(),
            (item["tts_speech"] * (2 ** 15)).numpy().astype(np.int16),
            cosyvoice.sample_rate,
            "raw"
        ).getvalue()
        yield b
        c += b
    
