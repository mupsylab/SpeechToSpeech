import torch
import numpy as np
import librosa
from modelscope.models.base.base_model import Model
from modelscope.models.audio.ans.frcrn import FRCRNDecorator
from modelscope.utils.audio.audio_utils import audio_norm

class FRCRN():
    def __init__(self, model_dir, device: str):
        model: FRCRNDecorator = Model.from_pretrained(model_dir)
        self.model: FRCRNDecorator = model.to(device)
        self.model.eval()
        self.device = device

    @torch.no_grad()
    def forward(self, x: np.ndarray, sr: int):
        """
        输入和输出应该都是numpy.ndarray! 待改
        x 应该是二维数组, 第一维是channel, 第二维是frame
        """
        if sr != 16000:
            # 必须用librosa, 不然降噪出问题。绝了
            x = librosa.resample(x, orig_sr=sr, target_sr=16000)
        x = audio_norm(x)
        x = torch.from_numpy(x).to(self.device).unsqueeze(0)
        _, t = x.shape
        window = 16000
        stride = int(window * 0.75)

        # 是否需要分段
        decode_do_segement = False
        if t > window * 120:
            # 超过2分钟的话
            decode_do_segement = True

        if t < window:
            x = torch.nn.functional.pad(x, (0, window - t))
        elif t < window + stride:
            x = torch.nn.functional.pad(x, (0, window + stride - t))
        elif (t - window) % stride != 0:
            # 无法整除，需要填充
            x = torch.nn.functional.pad(x, (0, t - (t - window) // stride * stride))

        if decode_do_segement:
            noise = torch.zeros(t, device="cpu") # 仅存储, 没必要放显卡
            voice = torch.zeros(t, device="cpu") # 仅存储, 没必要放显卡
            give_up_length = (window - stride) // 2
            currend_idx = 0
            while currend_idx + window <= t:
                tmp_input = dict(
                    noisy = x[:, currend_idx:currend_idx + window]
                )
                output = self.model(tmp_input)
                tmp_noise = output['wav_l1'][0].cpu()
                tmp_voice = output['wav_l2'][0].cpu()
                if currend_idx == 0:
                    noise[currend_idx:currend_idx + window - give_up_length] = tmp_noise[:-give_up_length]
                    voice[currend_idx:currend_idx + window - give_up_length] = tmp_voice[:-give_up_length]
                else:
                    noise[currend_idx + give_up_length:currend_idx + window - give_up_length] = tmp_noise[give_up_length:-give_up_length]
                    voice[currend_idx + give_up_length:currend_idx + window - give_up_length] = tmp_voice[give_up_length:-give_up_length]
                currend_idx += stride
        else:
            output = self.model(dict(noisy = x))
            noise = output['wav_l1'][0].cpu()
            voice = output['wav_l2'][0].cpu()
        noise = noise[:t].numpy()
        voice = voice[:t].numpy()
        if sr != 16000:
            noise = librosa.resample(noise, orig_sr=16000, target_sr=sr)
            voice = librosa.resample(voice, orig_sr=16000, target_sr=sr)
        return noise * (2 ** 15), voice * (2 ** 15)
