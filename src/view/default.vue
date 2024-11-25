<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { BaseAudioPlayer, StreamAudioPlayer, BaseAudioRecord, StreamAudioRecord, VisualAudio } from '../util/audio';
import { loadAudioFromGPT, sttFromSensorVoice } from '../util/TTS';

const ap = new BaseAudioPlayer();
const ar = new StreamAudioRecord((blob) => {
    sttFromSensorVoice(blob).then(r => {
        console.log(r[0]["text"]);
    });
});

const toggle = () => {
    if(ar.status === "recording") ar.stop(); else ar.start();
}

onMounted(() => {
    new VisualAudio({
        width: window.innerWidth,
        height: window.innerHeight
    }).start("#visualizer", ar, ap);
});

const msg = ref("");
const keyboardEvent = (e: KeyboardEvent) => {
    if(e.key === 'Enter') {
        loadAudioFromGPT(msg.value, ap);
        msg.value = "";
    }
}
</script>

<template>
    <div class="test-box">
        <div class="visualizer-container" @click="toggle">
            <canvas id="visualizer"></canvas>
        </div>
        <div class="input-text" @keydown="keyboardEvent">
            <input type="text" name="message" id="msg" v-model="msg" />
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
canvas {
    cursor: pointer;
}

.input-text {
    position: absolute;
    left: 50%;
    bottom: 16px;
    transform: translate(-50%, 0%);
}
.input-text input {
    width: 300px;
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