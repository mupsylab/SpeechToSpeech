import { BaseAudioPlayer, StreamAudioPlayer } from "./audio";

interface SensorVoiceResult {
    key: string,
    text: string,
    clean_text: string,
    raw_text: string
}

function loadBaseAudioFromGPT(s: string, ap: BaseAudioPlayer, url: string) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "arraybuffer";

    xhr.addEventListener("progress", () => {
        // 数据加载中
    });
    xhr.addEventListener("loadend", () => {
        // 数据加载完毕
        ap.play(xhr.response);
    });

    xhr.send(JSON.stringify({
        text: s,
        text_lang: "zh",
        ref_audio_path: "output/ssy_的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。.wav",
        prompt_text: "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。",
        prompt_lang: "zh"
    }));
}

function loadStreamAudioFromGPT(s: string, ap: StreamAudioPlayer, url: string) {
    const text_lang = "zh";
    const ref_audio_path = "output/ssy_的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。.wav";
    const prompt_lang = "zh";
    const prompt_text = "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。";
    const text_split_method = "cut5";
    const batch_size = 2;
    const media_type = "wav";
    const streaming_mode = true;
    const uri = `${url}?text=${s}&text_lang=${text_lang}&ref_audio_path=${ref_audio_path}&prompt_lang=${prompt_lang}&prompt_text=${prompt_text}&text_split_method=${text_split_method}&batch_size=${batch_size}&media_type=${media_type}&streaming_mode=${streaming_mode}`;

    ap.play(uri);
}

export function loadAudioFromGPT(s: string, ap: BaseAudioPlayer | StreamAudioPlayer, url: string = "https://chat.lan.mupsy.net/tts") {
    if (!s.length) return;
    if (ap instanceof BaseAudioPlayer) {
        loadBaseAudioFromGPT(s, ap, url);
    }

    if (ap instanceof StreamAudioPlayer) {
        loadStreamAudioFromGPT(s, ap, url);
    }
}

export function sttFromSensorVoice(blob: Blob, url: string = "https://chat.lan.mupsy.net/api/v1/asr") {
    return new Promise<SensorVoiceResult[]>((resolve) => {
        const formData = new FormData();
        const audioFile = new File([blob], "asd", { type: "audio/wav" });
        formData.append('files', audioFile);
        formData.append("keys", "asd")
        fetch(url, {
            method: "POST",
            body: formData
        }).then(r => r.json())
            .then(r => {
                resolve(r["result"]);
            });
    });
}