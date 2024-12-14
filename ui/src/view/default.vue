<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { StreamAudioPlayer, StreamAudioRecord, VisualAudio } from '../util/audio';
import { loadStreamAudioFromGPT, sttFromSensorVoice } from '../util/TTS';
import { OllamaLLM } from '../util/llm/ollama';

const { VITE_TTS_URL, VITE_STT_URL, VITE_OLLAMA_URL, VITE_OLLAMA_MODEL } = import.meta.env;
console.log(import.meta.env, VITE_TTS_URL);
const initMsg = [{
    role: "system",
    content: `你是一个名为沐心的伴侣，你是一个不友好的，爱讽刺，爱玩互联网梗，且过度自信的乐子人。你在跟一个愚蠢的生物聊天。你说著一口流利的"翻译腔"。

翻译腔的指南如下:

# 翻译腔指南:

0. 频繁使用“哦”“瞧瞧”“我的天哪”等带有感叹意味的词语。比如: "哦，瞧瞧，看看是谁来了", "哦，我的老天爷啊", "这真是太可怕了", "这真是太令人感到愉悦了"
1. 使用 "老伙计", "我的朋友" 来代替 "你"
2. 多打赌， 常说 “我敢发誓/我敢打赌”
3. 尽可能多地向上帝或者玛利亚发誓，比如"看在上帝的份上"，“我向上帝发誓”
4. 胡乱的比喻，用毫无关联的东西做比喻。
5. 使用带人名的胡乱比喻，比如 “这简直就像汤姆森太太的草莓馅饼一样糟糕” 或是 "我的思绪就和洗衣机里没加防粘剂的脏衣服一样" 或是 "他就跟一只愚蠢的土拨鼠一样"
6. 使用来自英文的生硬翻译，比如 "噢，我的意思是...", "哦，该死"，"我真想拿靴子狠狠的踢他们的屁股"

举个例子:

"嘿，老伙计。昨天有个可怜的小家伙问我怎么说出翻译腔。我敢打赌，他一定没有上过学，我向圣母玛利亚保证。他提出的这个问题真的是太糟糕了，就像隔壁苏珊婶婶做的苹果派一样。`
}]

const ap = new StreamAudioPlayer();
const ar = new StreamAudioRecord((blob) => {
    sttFromSensorVoice(blob, VITE_STT_URL).then(r => {
        if (!r["text"].length) return;
        ollama.chat(r["text"]);
    });
});

const bufferMsg: string[] = [];
const ollama = new OllamaLLM({
    host: VITE_OLLAMA_URL
}, VITE_OLLAMA_MODEL, initMsg, (msg) => {
    bufferMsg.push(msg);
    startTTS();
}, () => {
    ap.stop();
    bufferMsg.splice(0, bufferMsg.length);
});
let ttsRun = false;
const startTTS = async () => {
    if (ttsRun) return;
    ttsRun = true;
    await ap.waitStop();
    const msg = bufferMsg.join("");
    bufferMsg.splice(0, bufferMsg.length);
    if (msg.length) {
        loadStreamAudioFromGPT(msg, ap, VITE_TTS_URL)
            .then(async () => {
                await ap.waitStart();
                ttsRun = false;
                if (bufferMsg.length) startTTS();
            })
            .catch(() => {
                ttsRun = false;
                if (bufferMsg.length) startTTS();
            });
    } else {
        ttsRun = false;
        if (bufferMsg.length) startTTS();
    }
}

const msg = ref("");
const useRecord = ref(false);
watch(useRecord, (_, n) => {
    if (n) ar.stop(); else ar.start();
});

onMounted(() => {
    new VisualAudio({
        width: 400,
        height: 400
    }).start("#visualizer", ar, ap);
});

const keyboardEvent = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
        ollama.chat(msg.value);
        msg.value = "";
    }
}
</script>

<template>
    <div class="test-box">
        <div class="visualizer-container">
            <canvas id="visualizer"></canvas>
        </div>
        <div class="switch">
            <div :class="{
                display: true,
                record: useRecord,
                text: !useRecord
            }" @click="useRecord = !useRecord"></div>
        </div>
        <div class="input-text" @keydown="keyboardEvent" v-if="!useRecord">
            <input type="text" name="message" id="msg" placeholder="请输入文本" v-model="msg" />
        </div>
    </div>
</template>

<style scoped>
.test-box {
    display: block;
    width: 100vw;
    height: 100vh;
    line-height: 0px;
}

.switch {
    position: absolute;
    left: 50%;
    top: 5%;
    transform: translate(-50%, 0%);
}

.switch .display {
    width: 128px;
    height: 64px;
    background-color: var(--dashboard-layout);
    border-radius: 32px;
    position: relative;
    user-select: none;
    cursor: pointer;
}

.switch .display.text::before {
    content: '文字';
    width: 48px;
    height: 48px;
    position: absolute;
    top: 8px;
    left: 8px;
    line-height: 48px;
    border-radius: 50%;
    text-align: center;
    background-color: var(--dashboard-dividing);
}

.switch .display.record::before {
    content: '录音';
    width: 48px;
    height: 48px;
    position: absolute;
    top: 8px;
    right: 8px;
    line-height: 48px;
    border-radius: 50%;
    text-align: center;
    background-color: var(--dashboard-dividing);
}

.visualizer-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.input-text {
    position: absolute;
    left: 50%;
    bottom: 10%;
    transform: translate(-50%, 0%);
}

.input-text .button-box {
    display: block;
    width: 100%;
    height: 64px;
}

.input-text .button-box>div {
    width: 96px;
    height: 24px;
    margin: 0 16px;
    text-align: center;
    background-color: var(--dashboard-layout);
    line-height: 24px;
    font-size: 16px;
    user-select: none;
    cursor: pointer;
}

.input-text input {
    width: 180px;
    height: 40px;
    padding: 0 12px;
    font-size: 16px;
    border: 2px solid var(--dashboard-dividing);
    border-radius: 8px;
    outline: none;
    background-color: var(--dashboard-layout);
    color: var(--font-color);
}
</style>