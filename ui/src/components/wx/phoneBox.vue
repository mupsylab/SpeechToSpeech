<script setup lang="ts">
import { PhoneFilled } from '@element-plus/icons-vue';
import { ElAvatar, ElIcon } from 'element-plus';

const props = defineProps({
    phoneState: {
        type: Boolean,
        default: false
    },
    avator: {
        type: String,
        default: "./assets/avator/assistant.png"
    }
});
const emits = defineEmits(['togglePhone']);
</script>

<template>
    <div class="phone-box">
        <div class="avator">
            <ElAvatar class="avator-img" shape="square" :size="114" :src="props.avator" />
        </div>
        <div class="button">
            <slot></slot>
        </div>
        <div class="button">
            <ElIcon :class="{ phone: true, close: phoneState }" @click="emits('togglePhone');"><PhoneFilled /></ElIcon>
        </div>
    </div>
</template>

<style scoped>
.phone-box {
    background-color: var(--idegrey-3);
    vertical-align: middle;
}

.avator {
    width: 100%;
    padding: 100px 0 50px 0;
    text-align: center;
}
.avator .el-avatar {
    display: block;
    margin: auto;
}

.button {
    height: 64px;
    text-align: center;
    margin: 40px 0;
}
.phone {
    width: 64px;
    height: 64px;
    margin: 0 40px;
    background-color: var(--green-6) !important;
    transition: all 0.3s ease-in-out;
    color: var(--dark-idegrey-10) !important;
    font-size: 36px;
    border-radius: 50%;
    cursor: pointer;
}
.phone.close {
    transform: rotate(135deg);
    background-color: var(--red-6) !important;
}
</style>