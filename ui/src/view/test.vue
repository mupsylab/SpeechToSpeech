<script setup lang="ts">
import { onMounted } from 'vue';

class StreamAudioPlayer {
    private audioElement: HTMLAudioElement;
    private mediaSource: MediaSource;
    private sourceBuffer: SourceBuffer | null = null;
    private audioCtx: AudioContext | null = null;
    private isAppending: boolean = false; // 避免重复操作

    private queueCursor: number = -1;
    private queue: Uint8Array[] = [];

    constructor() {
        this.mediaSource = new MediaSource();
        this.audioElement = new Audio();
        this.audioElement.src = URL.createObjectURL(this.mediaSource);
        this.audioElement.addEventListener("timeupdate", this.timeHandler.bind(this));
    }

    private init(audio_type: string) {
        if (this.sourceBuffer) this.mediaSource.removeSourceBuffer(this.sourceBuffer);
        this.sourceBuffer = this.mediaSource.addSourceBuffer(audio_type);

        this.queue = [];
        this.queueCursor = -1;
        this.isAppending = false;
    }

    private timeHandler() {
        if (!this.sourceBuffer || this.isAppending) return;
        const currentTime = this.audioElement.currentTime;
        const bufferedStart = this.sourceBuffer.buffered.start(0);
        const bufferedEnd = this.sourceBuffer.buffered.end(0);

        console.log(
            currentTime, bufferedStart, bufferedEnd
        );
        if (bufferedEnd - currentTime < 2) {
            // 剩余可播放时间太短的话
            this.audioElement.pause();
        }

        // 如果当前剩余可播放时间较短
        if (bufferedEnd - currentTime < 10) {
            this.isAppending = true;
            this.sourceBuffer.addEventListener("updateend", () => {
                this.isAppending = false;
                this.addBuffer();
            }, { once: true });
            this.sourceBuffer.remove(bufferedStart, currentTime);
        }
    }
    private addBuffer() {
        if (!this.queue.length || !this.sourceBuffer || this.isAppending) return;
        const chunk = this.queue[this.queueCursor];
        this.isAppending = true;
        this.sourceBuffer.addEventListener("updateend", () => {
            this.isAppending = false;
            this.queueCursor += 1;
        });
        this.sourceBuffer.appendBuffer(chunk);
    }

    public async loadAudio(reader: ReadableStreamDefaultReader<Uint8Array>, audio_type: string) {
        if (this.mediaSource.readyState == "open") this.init(audio_type);
        else {
            this.mediaSource.addEventListener("sourceopen", () => {
                this.init(audio_type);
            });
        }
        while (true) {
            const { done, value } = await reader.read();
            if (done || !value) break;
            this.queue.push(value);
            if (this.queueCursor < 0) {
                this.queueCursor = 0;
                this.addBuffer();
            }
        }
    }

    public player() {
        if (!this.sourceBuffer?.buffered.length) return;
        if (!this.audioCtx) {
            this.audioCtx = new AudioContext();
            const sourceNode = this.audioCtx.createMediaElementSource(this.audioElement);
            sourceNode.connect(this.audioCtx.destination);
        }

        this.audioElement.play();
    }
    public stop() {
        this.audioElement.pause();
    }
}

const s = new StreamAudioPlayer();
const c = () => {
    // loadAudio();
    s.player();
};

onMounted(() => {
    fetch('/assets/audio/videoplayback.mp3', {
        method: 'GET',
    }).then(async (r) => {
        if (!r.body) return;
        const reader = r.body.getReader();
        s.loadAudio(reader, "audio/mpeg");
    });
});
</script>

<template>
    <div>
        <div @click.once="c">ccccc</div>
        <audio controls src="" id="audioPlayer"></audio>
    </div>
</template>
