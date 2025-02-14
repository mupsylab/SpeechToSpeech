import os
import re
import fastapi
import torchaudio
from fastapi.responses import JSONResponse
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from typing import List
from typing_extensions import Annotated

from .interface import Language
from ..utils.cache import cache

router = fastapi.APIRouter(prefix="/api")

from io import BytesIO
from model.SensorVoice.model import SenseVoiceSmall
def load_model1():
    return SenseVoiceSmall.from_pretrained(
        model = "iic/SenseVoiceSmall",
        device = os.getenv("SENSE_DEVICE", "cuda")
    )
m1, m1_kwargs = load_model1()
m1.eval()

@router.post("/asr/v1")
async def sensor_voice_asr(files: Annotated[List[bytes], fastapi.File(description="wav or mp3 audios in 16KHz")], 
                           keys: Annotated[str, fastapi.Form(description="name of each audio joined with comma")], 
                           lang: Annotated[Language, fastapi.Form(description="language of audio content")] = "auto"):
    audios = []
    audio_fs = 0
    for file in files:
        file_io = BytesIO(file)
        data_or_path_or_list, audio_fs = torchaudio.load(file_io)
        data_or_path_or_list = data_or_path_or_list.mean(0)
        audios.append(data_or_path_or_list)
        file_io.close()
    if lang == "":
        lang = "auto"
    if keys == "":
        key = ["wav_file_tmp_name"]
    else:
        key = keys.split(",")

    res = m1.inference(
        data_in = audios,
        language = lang,
        use_itn = False,
        ban_emo_unk = False,
        key = key,
        fs = audio_fs,
        **m1_kwargs
    )
    if len(res) == 0:
        return JSONResponse({ "result": [] })
    obj = {}
    for item in res[0]:
        obj["raw_text"] = item["text"]
        obj["text"] = rich_transcription_postprocess(item["text"])
        obj["clean_text"] = re.sub(r"<\|.*\|>", "", item["text"], 0, re.MULTILINE)
    return JSONResponse({
        "result": obj
    })

from funasr import AutoModel
m2: AutoModel = None
def load_model2():
    return AutoModel(
        model=os.getenv("SENSE_MODEL", "model_pretrained/SenseVoiceSmall"),
        trust_remote_code=True,
        remote_code="model/SensorVoice/model.py",
        vad_model=os.getenv("VAD_MODEL", "model_pretrained/speech_fsmn_vad_zh-cn-16k-common-pytorch"),
        vad_kwargs={"max_single_segment_time": 30000},
        device=os.getenv("SENSE_DEVICE", "cuda"),
    )
@router.post("/asr/v2")
async def sensor_voice_asr2(files: Annotated[List[fastapi.UploadFile], fastapi.File(description="wav or mp3 audios in 16KHz")],
                            lang: Annotated[Language, fastapi.Form(description="language of audio content")] = "auto"):
    global m2
    if m2 is None:
        m2 = load_model2()

    if lang == "":
        lang = "auto"

    audio_path = []
    for file in files:
        blob = await file.read()
        audio_path.append(cache.get_path(cache.save(blob)))

    res = m2.generate(
        input = audio_path,
        cache={},
        language=lang,
        use_itn=True,
        batch_size=1,
        merge_vad=True,
        merge_length_s=15
    )

    text = res[0]["text"]
    return JSONResponse({
        "result": {
            "raw_text": text,
            "text": rich_transcription_postprocess(text),
            "clean_text": re.sub(r"<\|.*\|>", "", text, 0, re.MULTILINE)
        }
    })


