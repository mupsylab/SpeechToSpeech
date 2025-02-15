<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { BaseAudioRecord, StreamAudioPlayer, VisualAudio } from '../util/audio';
import { useSystemConfig } from '../store/Config';

const config = useSystemConfig();

const ap = new StreamAudioPlayer();
ap.addEventListener("stop", () => {
    UserSpeech.value = true;
});

const ar = new BaseAudioRecord();
ar.addEventListener("record", async (blob) => {
    const form = new FormData();
    form.append("files", new File([blob], "key", { type: "audio/wav" }))
    form.append("keys", "key");
    form.append("lang", "zh");

    fetch(config.getURL("/api/asr"), {
        method: "POST",
        body: form
    })
    .then(r => r.text())
    .then(_ => {
        ap.play(config.getURL(`/api/tts`));
    });
});

onMounted(() => {
    new VisualAudio({
        width: 400,
        height: 400
    }).start("#visualizer", ar, ap);
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
/**
 * 下面是激活聊天, 避免错误
 */
const init = ref(false);

const click = () => {
    if (!init.value) {
        init.value = true;
        ap.play(config.getURL(`/api/tts`));
    } else {
        if (!UserSpeech.value) return;
        UserSpeech.value = false;
    }
}
</script>

<template>
    <div class="test-box">
        <div class="visualizer-container" @click="click">
            <canvas id="visualizer"></canvas>
        </div>
        <div class="tip" @click.stop="click">
            {{ !init ? "点击这里 开始聊天" : (UserSpeech ? "用户" : "机器人") }}
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

.visualizer-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
}

.tip {
    position: absolute;
    top: 50%; 
    left: 50%; 
    transform: translate(-50%, -50%); 
    cursor: pointer;
}
</style>