<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { StreamAudioPlayer, StreamAudioRecord, VisualAudio } from '../util/audio';
import { loadStreamAudioFromGPT, sttFromSensorVoice } from '../util/TTS';
import { OllamaLLM } from '../util/llm/ollama';

import * as config from "../config";

const ap = new StreamAudioPlayer();
const ar = new StreamAudioRecord((blob) => {
    sttFromSensorVoice(blob, config.sttURL).then(r => {
        if (!r["text"].length) return;
        ollama.chat(r["text"]);
    });
});

const bufferMsg: string[] = [];
const ollama = new OllamaLLM({
    host: config.ollamaURL
}, config.ollamaMODEL, config.initMsg, (msg) => {
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
        loadStreamAudioFromGPT(msg, ap, config.ttsURL)
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