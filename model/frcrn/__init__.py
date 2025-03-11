import torch
import numpy as np
import torchaudio
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
    def forward(self, x: torch.FloatTensor, sr: int):
        """
        输入和输出应该都是numpy.ndarray! 待改
        x 应该是二维数组, 第一维是channel, 第二维是frame
        """
        if sr != 16000:
            x = torchaudio.transforms.Resample(
                orig_freq = sr,
                new_freq = 16000,
                resampling_method = "sinc_interp_kaiser",
                lowpass_filter_width = 64,
                rolloff = 0.9475937167399596,
                beta = 14.769656459379492
            )(x)
        x = audio_norm(x)
        x = x.unsqueeze(0).to(self.device)
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
            voice = torch.zeros(t, device="cpu") # 仅存储, 没必要放显卡
            give_up_length = (window - stride) // 2
            currend_idx = 0
            while currend_idx + window <= t:
                tmp_input = dict(
                    noisy = x[:, currend_idx:currend_idx + window]
                )
                output = self.model(tmp_input)
                tmp_voice = output['wav_l2'][0].cpu()
                if currend_idx == 0:
                    voice[currend_idx:currend_idx + window - give_up_length] = tmp_voice[:-give_up_length]
                else:
                    voice[currend_idx + give_up_length:currend_idx + window - give_up_length] = tmp_voice[give_up_length:-give_up_length]
                currend_idx += stride
        else:
            output = self.model(dict(noisy = x))
            voice = output['wav_l2'][0].cpu()
        voice = voice[:t]
        if sr != 16000:
            voice = torchaudio.transforms.Resample(
                orig_freq = 16000,
                new_freq = sr,
                resampling_method = "sinc_interp_kaiser",
                lowpass_filter_width = 64,
                rolloff = 0.9475937167399596,
                beta = 14.769656459379492
            )(voice)
        return voice * (2 ** 15)
