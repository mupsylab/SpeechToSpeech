<script setup lang="ts">
import { Mute, Microphone, ChatDotSquare } from '@element-plus/icons-vue';
import { ElIcon, ElMessage } from 'element-plus';
import ChatBox from '../../components/wx/chatBox.vue';
import PhoneBox from '../../components/wx/phoneBox.vue';
import { Ref, ref } from 'vue';
import { AudioPlayer } from '../../util/audio/AudioPlayer';
import { AudioRecord } from '../../util/audio/AudioRecord';
import { useUserInfo } from '../../store/UserInfo';
import { base64ToArrayBuffer } from '../../util/audio/utils';

const userInfo = useUserInfo();

let ws: WebSocket | undefined;
const ap = new AudioPlayer();
const ar = new AudioRecord();
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
function connectWS() {
    ws = new WebSocket(`/ws/${userInfo.session_id}`);
    ws.addEventListener("error", () => {
        ElMessage.error("连接失败，请刷新重试");
        phone.value = false;
        ar.stop();
        ap.stop();
    });
    ws.addEventListener("close", () => {
        phone.value = false;
        ar.stop();
        ap.stop();
    });
    ws.addEventListener("open", () => {
        ar.start().then(() => {
            ws?.send(JSON.stringify({
                action: "init",
                param: { sampleRate: ar?.sampleRate }
            }));
        });
    });
    ws.addEventListener("message", (e) => {
        if (e.data == "tts:start") {
            ap.start();
        } else if (e.data == "tts:stop") {
            ap.stop();
        } else if (e.data.startsWith("stream:asr")) {
            putMsg("user", e.data.replace("stream:asr:", ""));
        } else if (e.data.startsWith("stream:llm")) {
            putMsg("assistant", e.data.replace("stream:llm:", ""));
        } else if (e.data.startsWith("stream:tts")) {
            const base64 = e.data.replace("stream:tts:", "");
            ap.load(base64ToArrayBuffer(base64));
        }
    });
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
const togglePhone = () => {
    phone.value = !phone.value;
    if (phone.value) {
        connectWS();
        muted.value = false;
    } else {
        ws?.close();
    }
};
const muted = ref(true);
const toggleMute = () => {
    muted.value = !muted.value;
    if (muted.value) {
        ar?.stop();
    } else {
        ar?.start();
    }
};
const chat = ref(false);
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