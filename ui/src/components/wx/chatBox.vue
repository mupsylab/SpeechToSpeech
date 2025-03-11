<script setup lang="ts">
const props = defineProps({
    messages: {
        type: Array<{"role": string, "msg": string}>
    }
})
</script>

<template>
    <div class="chat-box">
        <template v-for="item in props.messages">
            <div class="messages"
                :class="{ 'self': item.role === 'user', 'other': item.role === 'assistant' }">
                <div>{{ item.msg }}</div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.chat-box {
    padding: 20px;
    background-color: var(--idegrey-3);
    box-sizing: border-box;
    vertical-align: middle;
}

.messages div {
    display: inline-block;
    margin: 7px 0 7px 0;
    padding: 10px 10px;
    background-color: var(--idegrey-5);
    border-radius: 10px 10px 10px 0px;
    box-sizing: border-box;
    color: var(--idegrey-9);
}
.messages.self {
    text-align: right;
}
.messages.self div {
    background-color: var(--green-6);
    border-radius: 10px 10px 0px 10px;
}
</style>