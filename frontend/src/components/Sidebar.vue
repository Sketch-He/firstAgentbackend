<script setup lang="ts">
import type { ConversationSummary } from "../types/chat";

defineProps<{
  conversations: ConversationSummary[];
  currentId: string | null;
  isLoading: boolean;
}>();

const emit = defineEmits<{
  create: [];
  select: [id: string];
  delete: [id: string];
  knowledge: [];
}>();

function formatTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 7) return `${diffDay} 天前`;

  return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">对话历史</h2>
      <div class="sidebar-header-actions">
        <button
          type="button"
          class="sidebar-knowledge-btn"
          title="知识库"
          @click="emit('knowledge')"
        >
          📚
        </button>
        <button
          type="button"
          class="sidebar-new-btn"
          @click="emit('create')"
        >
          + 新对话
        </button>
      </div>
    </div>

    <div class="sidebar-list">
      <p v-if="isLoading" class="sidebar-empty">加载中...</p>
      <p v-else-if="conversations.length === 0" class="sidebar-empty">暂无对话</p>

      <button
        v-for="conv in conversations"
        :key="conv.id"
        type="button"
        :class="['sidebar-item', { active: conv.id === currentId }]"
        @click="emit('select', conv.id)"
      >
        <span class="sidebar-item-title">{{ conv.title }}</span>
        <span class="sidebar-item-time">{{ formatTime(conv.updated_at) }}</span>
        <span
          class="sidebar-item-delete"
          role="button"
          tabindex="0"
          title="删除对话"
          @click.stop="emit('delete', conv.id)"
          @keydown.enter.stop="emit('delete', conv.id)"
        >
          ×
        </span>
      </button>
    </div>
  </aside>
</template>
