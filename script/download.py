import requests
from modelscope import snapshot_download

# SDK模型下载
snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', local_dir='model_pretrained/speech_fsmn_vad_zh-cn-16k-common-pytorch')
snapshot_download('iic/speech_frcrn_ans_cirm_16k', local_dir='model_pretrained/speech_frcrn_ans_cirm_16k')
snapshot_download('iic/SenseVoiceSmall', local_dir='model_pretrained/SenseVoiceSmall')
snapshot_download('iic/CosyVoice2-0.5B', local_dir='model_pretrained/CosyVoice2-0.5B')
snapshot_download('iic/CosyVoice-ttsfrd', local_dir='model_pretrained/CosyVoice-ttsfrd')

# GPT_SoVITS模型下载
# 手动到 https://nas.lan.mupsy.net/sharing/oWN3u422f 下载，然后放到`model_pretrained`目录下，再解压！
