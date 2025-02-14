<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useSystemConfig } from '../store/Config';
import { ElButton } from 'element-plus';

const config = useSystemConfig();

const cid = ref<number>(-1);
fetch(config.getURL("/api/id"))
    .then(r => r.text())
    .then(r => {
        cid.value = parseInt(r);
    });

const router = useRouter();
const start = () => {
    router.push(`/manual/${cid.value}`);
}
</script>

<template>
    <div style="text-align: center;">
        <div>{{ cid }}</div>
        <ElButton :disabled="cid < 0" @click="start">继续</ElButton>
    </div>
</template>

<style lang="css" scoped>

</style>