<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { BaseAudioRecord, StreamAudioPlayer, VisualAudio } from '../util/audio';
import { useSystemConfig } from '../store/Config';
import { useRoute } from 'vue-router';

const config = useSystemConfig();
const route = useRoute();
const cid = route.params.cid as string;

const ap = new StreamAudioPlayer();
ap.addEventListener("stop", () => {
    UserSpeech.value = true;
});

const ar = new BaseAudioRecord();
ar.addEventListener("record", async (blob) => {
    const form = new FormData();
    form.append("files", new File([blob], "key", { type: "audio/wav" }))
    form.append("keys", "key");
    form.append("cid", cid);
    form.append("lang", "zh");

    fetch(config.getURL("/api/asr"), {
        method: "POST",
        body: form
    })
    .then(r => r.text())
    .then(_ => {
        ap.play(config.getURL(`/api/tts?cid=${cid}`));
    });
});

onMounted(() => {
    new VisualAudio({
        width: 400,
        height: 400
    }).start("#visualizer", ar, ap);
    ap.play(config.getURL(`/api/tts?cid=${cid}`));
});

/**
 * 下面的是判断轮到 用户 还是 机器人 说话
 */
const UserSpeech = ref<boolean>(false);
watch(UserSpeech, (n) => {
    if (n) {
        ar.start();
    }
    else {
        ar.stop();
    }
});
const click = () => {
    if (!UserSpeech.value) return;
    UserSpeech.value = false;
};
</script>

<template>
    <div class="test-box">
        <div class="visualizer-container">
            <canvas id="visualizer"></canvas>
        </div>
        <div class="switch">
            <div :class="{
                display: true,
                left: UserSpeech,
                right: !UserSpeech
            }" @click="click"></div>
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

.switch .display.left::before {
    content: '用户';
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

.switch .display.right::before {
    content: '研究者';
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