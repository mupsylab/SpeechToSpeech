<script setup lang="ts">
import { Mute, Microphone, ChatDotSquare } from '@element-plus/icons-vue';
import { ElIcon, ElMessage } from 'element-plus';
import ChatBox from '../../components/wx/chatBox.vue';
import PhoneBox from '../../components/wx/phoneBox.vue';
import { Ref, ref } from 'vue';
import { AudioPlayer } from '../../util/audio/AudioPlayer';
import { StreamAudioRecord } from '../../util/audio/AudioRecord';
import { useUserInfo } from '../../store/UserInfo';

const userInfo = useUserInfo();

let ws: WebSocket | undefined;
let ap: AudioPlayer | undefined, ar: StreamAudioRecord | undefined;
function startPhone() {
    ap = new AudioPlayer();
    ar = new StreamAudioRecord();
    ar.addEventListener("record", async (blob) => {
        const fileReader = new FileReader();
        fileReader.addEventListener("loadend", () => {
            const base64Audio = (fileReader.result as string).split(",")[1];
            ws?.send(JSON.stringify({
                action: "record",
                param: {
                    audio: base64Audio
                }
            }));
        });
        fileReader.readAsDataURL(blob);
    });
    ar.addEventListener("stop", () => {
        ws?.send(JSON.stringify({
            action: "finish"
        }));
    });
    // 开启麦克风
    ar.start();
    muted.value = false;

    ws = new WebSocket(`/ws/${userInfo.session_id}`);
    ws.addEventListener("error", () => {
        ElMessage.error("连接失败");
        togglePhone();
    });
    ws.addEventListener("close", () => {
        phone.value = false;
        stopPhone();
    })
    ws.addEventListener("open", () => {
        ws?.send(JSON.stringify({
            action: "init",
            param: {
                sampleRate: ar?.sampleRate
            }
        }));
        ap?.load(`/api/tts`);
        ap?.start();
    });
    ws.addEventListener("message", (e) => {
        if (e.data == "tts:start") {
            ap?.stop();
            ap?.load(`/api/tts`);
            ap?.start();
        } else if (e.data == "tts:stop") {
            ap?.stop();
        } else if (e.data.startsWith("stream:llm")) {
            putMsg("assistant", e.data.replace("stream:llm:", ""));
        } else if (e.data.startsWith("stream:asr")) {
            putMsg("user", e.data.replace("stream:asr:", ""));
        }
    });
}

function stopPhone() {
    ws?.close();
    ap?.stop();
    ap = undefined;
    ar?.stop();
    ar = undefined;
}

const messages: Ref<Array<{role: "user" | "assistant", msg: string}>> = ref([]);
function putMsg(role: "user" | "assistant", msg: string) {
    if (messages.value.length && messages.value[messages.value.length-1].role == role) {
        messages.value[messages.value.length-1].msg += msg;
    } else {
        messages.value.push({ role, msg });
    }
}
fetch("/api/history")
    .then(r => r.json())
    .then(r => {
        for (const msg of r.history) {
            putMsg(msg.role, msg.content);
        }
    });

const phone = ref(false);
const muted = ref(true);
const chat = ref(false);
const togglePhone = () => {
    phone.value = !phone.value;
    if (phone.value) {
        startPhone();
    } else {
        stopPhone();
    }
};
const toggleMute = () => {
    muted.value = !muted.value;
    if (muted.value) {
        ar?.stop();
    } else {
        ar?.start();
    }
};
const toggleChat = () => { chat.value = !chat.value; };
</script>

<template>
    <div class="box">
        <PhoneBox :phone-state="phone" @toggle-phone="togglePhone">
            <ElIcon :class="{ mute: muted }" @click="toggleMute" size="36">
                <Microphone v-if="!muted" />
                <Mute v-else />
            </ElIcon>
            <ElIcon class="phone" @click="toggleChat" size="36">
                <ChatDotSquare />
            </ElIcon>
        </PhoneBox>
        <div class="chat-box-layout" @click="toggleChat" :class="{
            show: chat
        }"></div>
        <ChatBox :class="{
            show: chat
        }" :messages="messages"></ChatBox>
    </div>
</template>

<style scoped>
.box {
    display: block;
    width: 800px;
    height: 600px;
    user-select: none;
    overflow: hidden;
}
.phone-box {
    display: inline-block;
    width: 300px;
    height: 100%;
}
.phone-box .el-icon {
    width: 64px;
    height: 64px;
    margin: 0 40px;
    background-color: var(--idegrey-5);
    color: var(--font-color);
    border-radius: 50%;
    cursor: pointer;
}
.phone-box .el-icon.mute { background-color: var(--fc-warn-bg); }

.chat-box-layout {
    display: none;
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
}
.chat-box {
    display: inline-block;
    width: 500px;
    height: 100%;
    overflow-y: auto;
}

.phone {
    display: none;
}
@media screen and (max-width: 400px) {
    html {
        overflow: hidden;
    }

    .box {
        display: block;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
    }
    .phone-box {
        width: 100%;
        height: 100%;
    }
    .chat-box {
        display: block;
        width: 100%;
        height: 0%;
        position: absolute;
        top: 100%;
        left: 0;
        padding: 0;
        transition: all 0.3s ease-in-out;
    }

    .chat-box-layout.show {
        display: block;
    }
    .chat-box.show {
        display: block;
        height: 75%;
        top: 25%;
        padding: 20px;
    }

    .phone {
        display: inline-flex;
    }
}
</style>