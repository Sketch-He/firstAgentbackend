<script setup lang="ts">
import { ref } from "vue";
import type { RagSource } from "../types/chat";

defineProps<{
  sources: RagSource[];
}>();

const expanded = ref(false);
</script>

<template>
  <div v-if="sources.length > 0" class="source-bubble">
    <button
      type="button"
      class="source-toggle"
      @click="expanded = !expanded"
    >
      <span class="source-icon">📚</span>
      <span class="source-label">参考了 {{ sources.length }} 个文档片段</span>
      <span :class="['source-arrow', { expanded }]">▼</span>
    </button>

    <div v-if="expanded" class="source-list">
      <div
        v-for="(source, index) in sources"
        :key="`${source.document_id}-${source.chunk_index}`"
        class="source-item"
      >
        <div class="source-item-header">
          <span class="source-filename">{{ source.filename }}</span>
          <span class="source-chunk">片段 {{ source.chunk_index + 1 }}</span>
        </div>
        <p class="source-snippet">{{ source.snippet }}</p>
      </div>
    </div>
  </div>
</template>
