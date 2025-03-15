from modelscope import snapshot_download

# SDK模型下载
snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', local_dir='model_pretrained/speech_fsmn_vad_zh-cn-16k-common-pytorch')
snapshot_download('iic/speech_frcrn_ans_cirm_16k', local_dir='model_pretrained/speech_frcrn_ans_cirm_16k')
snapshot_download('iic/SenseVoiceSmall', local_dir='model_pretrained/SenseVoiceSmall')
snapshot_download('iic/CosyVoice2-0.5B', local_dir='model_pretrained/CosyVoice2-0.5B')
snapshot_download('iic/CosyVoice-ttsfrd', local_dir='model_pretrained/CosyVoice-ttsfrd')

import zipfile
import requests
# GPT_SoVITS模型下载
session = requests.Session()
session.headers.update({
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
})
session.get("https://nas.hk1.mupsy.net/sharing/oWN3u422f")
resp = session.get(
    "https://nas.lan.mupsy.net/fsdownload/oWN3u422f/GPT_SoVITS.zip",
    stream=True
)
with open("model_pretrained/GPT_SoVITS.zip", "wb") as f:
    l = 0
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        f.write(chunk)
        l += len(chunk)
        print("\r%s - %s" % (l, resp.headers["content-length"]))

with zipfile.ZipFile('model_pretrained/GPT_SoVITS.zip', 'r') as zip_ref:
    zip_ref.extractall("model_pretrained/GPT_SoVITS")
