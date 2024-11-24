<script setup lang="ts">
import { onMounted } from 'vue';
import { BaseAudioPlayer, StreamAudioPlayer, BaseAudioRecord, StreamAudioRecord, VisualAudio } from '../util/audio';

const ap = new BaseAudioPlayer();
const ar = new StreamAudioRecord((blob) => {
    const formData = new FormData();
    const audioFile = new File([blob], "asd", { type: "audio/wav" });
    formData.append('files', audioFile);
    formData.append("keys", "asd")
    fetch("http://172.16.192.35:8000/api/v1/asr", {
        method: "POST",
        body: formData
    })
        .then(r => r.json())
        .then(r => {
            const text = r["result"][0]["text"];
            if(text) ap.loadAudioFromGPT("又臭又长的文本测试");
        });
});

const toggle = () => {
    if(ar.status === "recording") ar.stop(); else ar.start();
}

onMounted(() => {
    new VisualAudio().start("#visualizer", ar, ap);
});
</script>

<template>
    <div class="test-box">
        <div class="visualizer-container" @click="toggle">
            <canvas id="visualizer" width="400" height="400"></canvas>
        </div>
    </div>
</template>

<style scoped>
canvas {
    cursor: pointer;
}
</style>