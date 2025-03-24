/**
 * int16 转换为 float32
 */
export function int16ToFloat32(int16Array: Int16Array) {
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) { float32Array[i] = int16Array[i] / 0x8000; }
    return float32Array;
}

/**
 * 将 base64 编码的音频数据转换为 audiobuffer
 * @param base64 
 * @returns 
 */
export function base64ToArrayBuffer(base64: string) {
    const binary = atob(base64);
    const array = [];
    for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
    }
    return new Uint8Array(array).buffer;
}

/**
 * 音频二进制数据转换为 base64
 * @param blob 
 * @returns 
 */
export function blobToBase64(blob: Blob) {
    return new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onload = () => {
            const base64 = (reader.result as string).split(",")[1];
            resolve(base64);
        };
        reader.onerror = reject;
    });
}

/**
 * float32 格式转换为 int16，并保存为 ArrayBuffer
 * 获取二进制数据，可用 `new Blob([new DataView()])` 的方案
 * @param float32Array 
 * @returns 
 */
export function floatTo16BitPCM(float32Array: Float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return { buffer, view };
}

/**
 * 重采样音频数据到指定采样率
 * @param float32Array 
 * @param targetSamples 
 * @returns 
 */
export function resampleAudioData(float32Array: Float32Array, targetSamples: number) {
    if (targetSamples === float32Array.length) {
        return float32Array;
    }

    // Apply playback rate by resampling into a new buffer
    const resampledBuffer = new Float32Array(targetSamples);
    const playbackRate = float32Array.length / targetSamples;

    for (let i = 0; i < targetSamples; ++i) {
        const originalIndex = i * playbackRate;
        const start = Math.floor(originalIndex);
        const end = Math.ceil(originalIndex);

        if (start === end || end >= float32Array.length) {
            // If the start and end are the same or out of bounds, just use the start value
            resampledBuffer[i] = float32Array[start];
        } else {
            // Linear interpolation between two samples
            const ratio = originalIndex - start;
            resampledBuffer[i] = float32Array[start] * (1 - ratio) + float32Array[end] * ratio;
        }
    }

    return resampledBuffer;
}


/**
 * 合并 float32 音频数据
 * @param float32Arrays 
 * @returns 
 */
export function mergeAudioData(float32Arrays: Array<Float32Array>) {
    let samples = 0;
    for (let i = 0; i < float32Arrays.length; ++i) {
        samples += float32Arrays[i].length;
    }

    const merged = new Float32Array(samples);
    let offset = 0;
    for (let i = 0; i < float32Arrays.length; ++i) {
        const chunk = float32Arrays[i];
        merged.set(chunk, offset);
        offset += chunk.length;
    }
    return merged;
}

/**
 * 合并 audioBuffer 音频数据
 * @param audioBuffers 
 * @returns 
 */
export function mergeAudioBuffer(audioBuffers: AudioBuffer[]) {
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

/**
 * 将音频的audioBuffer转换为wav格式
 * @param audioBuffer 
 * @returns 
 */
export function audioBufferToWav(audioBuffer: AudioBuffer) {
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

/**
 * 从 url 获取音频，并输出为 audioBuffer
 * @param url 
 * @returns 
 */
export function getAudioBufferFromURL(url: string): Promise<AudioBuffer> {
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

/**
 * 从 二进制数据 中获取 audioBuffer
 * @param b 
 * @returns 
 */
export function getAudioBufferFromBlob(b: Blob): Promise<AudioBuffer> {
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
