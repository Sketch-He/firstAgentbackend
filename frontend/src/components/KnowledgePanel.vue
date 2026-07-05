<script setup lang="ts">
import { ref } from "vue";
import type { DocumentInfo } from "../types/chat";

const props = defineProps<{
  documents: DocumentInfo[];
  isLoading: boolean;
  isUploading: boolean;
}>();

const emit = defineEmits<{
  upload: [file: File];
  delete: [id: string];
  retry: [id: string];
  close: [];
}>();

const fileInputRef = ref<HTMLInputElement | null>(null);
const dragOver = ref(false);

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function getStatusText(status: DocumentInfo["status"]): string {
  switch (status) {
    case "processing": return "处理中";
    case "ready": return "就绪";
    case "failed": return "失败";
    default: return status;
  }
}

function getStatusClass(status: DocumentInfo["status"]): string {
  switch (status) {
    case "processing": return "status-processing";
    case "ready": return "status-ready";
    case "failed": return "status-failed";
    default: return "";
  }
}

function triggerUpload() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) {
    emit("upload", file);
    input.value = "";
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault();
  dragOver.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) {
    emit("upload", file);
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault();
  dragOver.value = true;
}

function handleDragLeave() {
  dragOver.value = false;
}
</script>

<template>
  <div class="knowledge-panel">
    <div class="knowledge-header">
      <h3 class="knowledge-title">知识库</h3>
      <button
        type="button"
        class="knowledge-close"
        title="关闭"
        @click="emit('close')"
      >
        ×
      </button>
    </div>

    <div
      :class="['knowledge-dropzone', { 'drag-over': dragOver, uploading: isUploading }]"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @click="triggerUpload"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept=".pdf,.docx,.txt,.md"
        style="display: none"
        @change="handleFileChange"
      />
      <div class="dropzone-content">
        <span class="dropzone-icon">📄</span>
        <p v-if="isUploading" class="dropzone-text">正在上传...</p>
        <template v-else>
          <p class="dropzone-text">拖拽文件到此处或点击上传</p>
          <p class="dropzone-hint">支持 PDF、Word、TXT、Markdown，最大 10MB</p>
        </template>
      </div>
    </div>

    <div class="knowledge-list">
      <p v-if="isLoading" class="knowledge-empty">加载中...</p>
      <p v-else-if="documents.length === 0" class="knowledge-empty">暂无文档</p>

      <div
        v-for="doc in documents"
        :key="doc.id"
        class="document-item"
      >
        <div class="document-info">
          <span class="document-name" :title="doc.filename">{{ doc.filename }}</span>
          <span class="document-meta">
            {{ formatFileSize(doc.file_size) }}
            <template v-if="doc.status === 'ready'"> · {{ doc.chunk_count }} 个片段</template>
            · {{ formatTime(doc.created_at) }}
          </span>
          <span v-if="doc.status === 'failed' && doc.error_message" class="document-error">
            {{ doc.error_message }}
          </span>
        </div>
        <div class="document-actions">
          <span :class="['document-status', getStatusClass(doc.status)]">
            {{ getStatusText(doc.status) }}
          </span>
          <button
            v-if="doc.status === 'failed'"
            type="button"
            class="document-action-btn"
            title="重试"
            @click="emit('retry', doc.id)"
          >
            🔄
          </button>
          <button
            type="button"
            class="document-action-btn delete"
            title="删除"
            @click="emit('delete', doc.id)"
          >
            🗑
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
