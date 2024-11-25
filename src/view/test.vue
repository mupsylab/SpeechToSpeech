<script setup lang="ts">
import { onMounted } from 'vue';

async function streamAudio() {
    const audioPlayer = document.getElementById('audioPlayer') as HTMLAudioElement;
    const mediaSource = new MediaSource();

    audioPlayer.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', async () => {
        const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg'); // 假设音频是 MP3 格式

        const MAX_BUFFER_DURATION = 10; // 保留 10 秒的音频数据
        let isAppending = false;

        audioPlayer.addEventListener('timeupdate', () => {
            if (!isAppending && sourceBuffer.buffered.length > 0) {
                const currentTime = audioPlayer.currentTime;
                const bufferedStart = sourceBuffer.buffered.start(0);

                console.log(222)
                // 清理已播放的数据，保留当前播放点附近的缓冲
                if (currentTime - bufferedStart > MAX_BUFFER_DURATION) {
                    sourceBuffer.remove(bufferedStart, currentTime - MAX_BUFFER_DURATION);
                }
            }
        });

        try {
            const response = await fetch('/assets/audio/videoplayback.mp3', {
                method: 'GET',
            });

            if (!response.body) {
                console.error('Response body is null.');
                return;
            }

            const reader = response.body.getReader();
            let receivedLength = 0;

            const processChunk = async ({ done, value }: ReadableStreamReadResult<Uint8Array>) => {
                if (done) {
                    mediaSource.endOfStream();
                    return;
                }

                if (value) {
                    receivedLength += value.length;

                    isAppending = true;
                    // 等待缓冲区更新完成
                    await new Promise<void>((resolve, reject) => {
                        sourceBuffer.addEventListener('updateend', () => {
                            isAppending = false;
                            resolve();
                        }, { once: true });
                        sourceBuffer.addEventListener('error', reject, { once: true });

                        try {
                            sourceBuffer.appendBuffer(value);
                        } catch (error) {
                            console.error('Buffer append error:', error);
                            reject(error);
                        }
                    });
                }

                const nextChunk = await reader.read();
                await processChunk(nextChunk);
            };

            const firstChunk = await reader.read();
            await processChunk(firstChunk);

        } catch (error) {
            console.error('Streaming error:', error);
            mediaSource.endOfStream('decode');
        }
    });

    mediaSource.addEventListener('error', (e) => {
        console.error('MediaSource error:', e);
    });
}

const c = () => {
    streamAudio();
};
</script>

<template>
    <div>
        <div @click.once="c">ccccc</div>
        <audio controls src="" id="audioPlayer"></audio>
    </div>
</template>
