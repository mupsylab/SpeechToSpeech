export class AudioUtils {
    public static audioBufferToWav(audioBuffer: AudioBuffer) {
        const numChannels = audioBuffer.numberOfChannels;
        const sampleRate = audioBuffer.sampleRate;
        const length = audioBuffer.length * numChannels * 2 + 44; // WAV header size + data size
        const buffer = new ArrayBuffer(length);
        const view = new DataView(buffer);

        function writeString(view: DataView, offset: number, string: string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }
        // Write WAV header
        writeString(view, 0, 'RIFF'); // ChunkID
        view.setUint32(4, length - 8, true); // ChunkSize
        writeString(view, 8, 'WAVE'); // Format
        writeString(view, 12, 'fmt '); // Subchunk1ID
        view.setUint32(16, 16, true); // Subchunk1Size
        view.setUint16(20, 1, true); // AudioFormat (PCM)
        view.setUint16(22, numChannels, true); // NumChannels
        view.setUint32(24, sampleRate, true); // SampleRate
        view.setUint32(28, sampleRate * numChannels * 2, true); // ByteRate
        view.setUint16(32, numChannels * 2, true); // BlockAlign
        view.setUint16(34, 16, true); // BitsPerSample
        writeString(view, 36, 'data'); // Subchunk2ID
        view.setUint32(40, length - 44, true); // Subchunk2Size

        // Write PCM data
        let offset = 44;
        for (let channel = 0; channel < numChannels; channel++) {
            const channelData = audioBuffer.getChannelData(channel);
            for (let i = 0; i < channelData.length; i++) {
                const sample = Math.max(-1, Math.min(1, channelData[i]));
                view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
                offset += 2;
            }
        }

        return buffer;
    }

    public static getAudioBufferFromURL(url: string): Promise<AudioBuffer> {
        return new Promise((resolve) => {
            fetch(url).then((r: Response) => {
                r.arrayBuffer().then(ab => {
                    const ac = new AudioContext();
                    ac.decodeAudioData(ab, function (audioBuffer) {
                        ac.close();
                        resolve(audioBuffer);
                    });
                });
            })
        });
    }
    public static getAudioBufferFromBlob(b: Blob): Promise<AudioBuffer> {
        return new Promise((resolve) => {
            b.arrayBuffer().then(ab => {
                const ac = new AudioContext();
                ac.decodeAudioData(ab, function (audioBuffer) {
                    ac.close();
                    resolve(audioBuffer);
                });
            });
        });
    }
    public static mergeAudioBuffer(audioBuffers: AudioBuffer[]) {
        const channels = Math.max(...audioBuffers.map(item => item.numberOfChannels))
        const rate = Math.max(...audioBuffers.map(item => item.sampleRate))
        const frameCount = audioBuffers.reduce((a, c) => a + c.length, 0);

        // 用最小的channel、rate和frameCount 造audio
        const ac = new AudioContext();
        const newAudioBuffer = ac.createBuffer(channels, frameCount, rate);
        const anotherArray = new Float32Array(frameCount);
        for (let channel = 0; channel < channels; channel++) {
            // channels
            let last_index = 0;
            audioBuffers.forEach(audioBuffer => {
                const audiobuffer_tmp = audioBuffer.getChannelData(channel);

                const len = audioBuffer.sampleRate * audioBuffer.duration;
                anotherArray.set(audiobuffer_tmp, last_index);
                last_index += len;
            });
            newAudioBuffer.copyToChannel(anotherArray, channel, 0);
        }
        ac.close();
        return newAudioBuffer;
    }
}