<script setup lang="ts">
import type { ChatMessage } from "../types/chat";

defineProps<{
  message: ChatMessage;
}>();

const roleTextMap: Record<ChatMessage["role"], string> = {
  system: "系统",
  user: "用户",
  assistant: "助手",
  tool: "工具"
};
</script>

<template>
  <article :class="['message-bubble', message.role]">
    <p class="message-role">{{ roleTextMap[message.role] }}</p>
    <div class="message-content">
      <p v-for="(line, index) in message.content.split('\n')" :key="`${message.id}-${index}`">
        {{ line }}
      </p>
    </div>
  </article>
</template>
