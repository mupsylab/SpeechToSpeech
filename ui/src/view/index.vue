<script setup lang="ts">
import { useRouter } from "vue-router";
import { useUserInfo } from "../store/UserInfo";

const router = useRouter();
</script>

<template>
    <el-card class="login-box">
        <el-button class="form-button" @click="router.push('/auto')">auto</el-button>
        <el-button class="form-button" @click="useUserInfo().login()">login</el-button>
    </el-card>
</template>

<style scoped>
.login-box {
    width: 400px;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-title {
    text-align: center;
    margin-bottom: 20px;
    color: #303133;
}

.form-button {
    display: block;
    width: 100%;
    box-sizing: border-box;
    margin: 20px auto;
}
</style>