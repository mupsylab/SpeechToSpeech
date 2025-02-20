import re
import numpy as np
import torch
import torchaudio
from io import BytesIO
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from enum import Enum
class Language(str, Enum):
    auto = "auto"
    zh = "zh"
    en = "en"
    yue = "yue"
    ja = "ja"
    ko = "ko"
    nospeech = "nospeech"

from pydantic import BaseModel
class Response(BaseModel):
    raw_text: str
    text: str
    clean_text: str

import os
from funasr import AutoModel
def load_model():
    return AutoModel(
        model=os.getenv("SENSE_MODEL", "model_pretrained/SenseVoiceSmall"),
        trust_remote_code=True,
        remote_code="model/SensorVoice/model.py",
        vad_model=os.getenv("VAD_MODEL", "model_pretrained/speech_fsmn_vad_zh-cn-16k-common-pytorch"),
        vad_kwargs={"max_single_segment_time": 30000},
        device=os.getenv("SENSE_DEVICE", "cuda"),
    )
model: AutoModel = load_model()

def asr(file_wav: bytes, lang: Language = "auto"):
    file_io = BytesIO(file_wav)
    data_or_path_or_list, audio_fs = torchaudio.load(file_io)
    data_or_path_or_list = data_or_path_or_list.mean(0)
    file_io.close()

    res = model.model.inference(data_in = [data_or_path_or_list],
                                language = lang,
                                use_itn = False,
                                ban_emo_unk = False,
                                fs = audio_fs,
                                **model.kwargs)
    torch.cuda.empty_cache()
    for item in res[0]:
        return Response(
            raw_text = item["text"],
            text = rich_transcription_postprocess(item["text"]),
            clean_text = re.sub(r"<\|.*\|>", "", item["text"], 0, re.MULTILINE),
        )

def asr_adv(file_path: str, lang: Language = "auto"):
    if not os.path.exists(file_path):
        return {}

    res = model.generate([file_path], cache = {},
                         lanuage = lang, use_itn=True,
                         batch_size=1,
                         merge_vad=True, merge_length_s=15)
    text = res[0]["text"]
    return Response(
        raw_text = text,
        text = rich_transcription_postprocess(text),
        clean_text = re.sub(r"<\|.*\|>", "", text, 0, re.MULTILINE)
    )

def asr_array(array: np.ndarray, sampleRate: int, lang: Language = "auto"):
    res = model.model.inference(data_in = torch.from_numpy(array),
                                language = lang,
                                fs = sampleRate,
                                use_itn = False,
                                ban_emo_unk = False,
                                **model.kwargs)
    torch.cuda.empty_cache()
    for item in res[0]:
        return Response(
            raw_text = item["text"],
            text = rich_transcription_postprocess(item["text"]),
            clean_text = re.sub(r"<\|.*\|>", "", item["text"], 0, re.MULTILINE),
        )

from typing import Tuple, List

VADItem = List[dict[str, List[List[int]]]]
VADParam = dict[str, float]

def vad_array(array: np.ndarray, sampleRate: int) -> Tuple[VADItem, VADParam]:
    [items, param] = model.vad_model.inference(data_in = [array], key = ["temp"], fs = sampleRate, **model.vad_kwargs)
    torch.cuda.empty_cache()
    return items, param
