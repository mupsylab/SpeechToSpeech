<script setup lang="ts">

import { onMounted } from 'vue';
async function streamAudio() {
    const audioPlayer = document.getElementById('audioPlayer') as HTMLAudioElement;
    const mediaSource = new MediaSource();

    audioPlayer.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', async () => {
        const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg'); // 假设音频是 MP3 格式
        const response = await fetch('/assets/audio/videoplayback.mp3', {
            method: 'GET',
            // headers: { 'Content-Type': 'application/json' },
            // body: JSON.stringify({ key: 'value' }) // 根据实际 API 的需求发送数据
        });

        const reader = (response.body as ReadableStream).getReader();
        let receivedLength = 0;

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                mediaSource.endOfStream();
                break;
            }

            receivedLength += value.length;
            sourceBuffer.appendBuffer(value);
        }
    });

    mediaSource.addEventListener('error', (e) => {
        console.error('MediaSource error:', e);
    });
}

onMounted(() => {streamAudio();})
</script>

<template>
    <div>
        <audio controls src="" id="audioPlayer"></audio>
    </div>
</template>