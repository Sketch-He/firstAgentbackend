import { ref, onMounted, onUnmounted } from "vue";
import type { DocumentInfo } from "../types/chat";
import {
  listDocuments as apiListDocuments,
  getDocument as apiGetDocument,
  uploadDocument as apiUploadDocument,
  deleteDocument as apiDeleteDocument,
  retryDocument as apiRetryDocument
} from "../lib/chatApi";

export function useDocuments() {
  const documents = ref<DocumentInfo[]>([]);
  const isLoading = ref(false);
  const isUploading = ref(false);
  const error = ref<string | null>(null);

  // 轮询相关
  let pollingTimer: ReturnType<typeof setInterval> | null = null;
  const processingIds = ref<Set<string>>(new Set());

  async function loadDocuments() {
    isLoading.value = true;
    error.value = null;
    try {
      documents.value = await apiListDocuments();
      // 找出所有 processing 状态的文档，开始轮询
      for (const doc of documents.value) {
        if (doc.status === "processing") {
          processingIds.value.add(doc.id);
        }
      }
      startPollingIfNeeded();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "加载文档列表失败。";
    } finally {
      isLoading.value = false;
    }
  }

  async function uploadDocument(file: File): Promise<DocumentInfo | null> {
    isUploading.value = true;
    error.value = null;
    try {
      const doc = await apiUploadDocument(file);
      documents.value = [doc, ...documents.value];
      // 开始轮询这个文档的状态
      if (doc.status === "processing") {
        processingIds.value.add(doc.id);
        startPollingIfNeeded();
      }
      return doc;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "文档上传失败。";
      return null;
    } finally {
      isUploading.value = false;
    }
  }

  async function deleteDocument(id: string): Promise<boolean> {
    error.value = null;
    try {
      await apiDeleteDocument(id);
      documents.value = documents.value.filter((d) => d.id !== id);
      processingIds.value.delete(id);
      stopPollingIfDone();
      return true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "删除文档失败。";
      return false;
    }
  }

  async function retryDocument(id: string): Promise<boolean> {
    error.value = null;
    try {
      const doc = await apiRetryDocument(id);
      const index = documents.value.findIndex((d) => d.id === id);
      if (index !== -1) {
        documents.value[index] = doc;
      }
      // 开始轮询
      processingIds.value.add(doc.id);
      startPollingIfNeeded();
      return true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "重试文档处理失败。";
      return false;
    }
  }

  // 轮询处理中的文档状态
  function startPollingIfNeeded() {
    if (pollingTimer !== null) return; // 已在轮询
    if (processingIds.value.size === 0) return; // 没有需要轮询的

    pollingTimer = setInterval(async () => {
      const idsToCheck = [...processingIds.value];
      for (const docId of idsToCheck) {
        try {
          const doc = await apiGetDocument(docId);
          // 更新本地列表中的文档状态
          const index = documents.value.findIndex((d) => d.id === docId);
          if (index !== -1) {
            documents.value[index] = doc;
          }
          // 如果不再是 processing，停止轮询这个文档
          if (doc.status !== "processing") {
            processingIds.value.delete(docId);
          }
        } catch {
          // 获取失败，可能是文档已被删除
          processingIds.value.delete(docId);
        }
      }
      // 所有文档都处理完了，停止轮询
      stopPollingIfDone();
    }, 2000); // 每 2 秒轮询一次
  }

  function stopPollingIfDone() {
    if (processingIds.value.size === 0 && pollingTimer !== null) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  }

  function stopAllPolling() {
    if (pollingTimer !== null) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
    processingIds.value.clear();
  }

  // 是否有已就绪文档
  const hasReadyDocuments = ref(false);

  function updateHasReadyDocuments() {
    hasReadyDocuments.value = documents.value.some((d) => d.status === "ready");
  }

  onMounted(() => {
    loadDocuments();
  });

  onUnmounted(() => {
    stopAllPolling();
  });

  return {
    documents,
    isLoading,
    isUploading,
    error,
    loadDocuments,
    uploadDocument,
    deleteDocument,
    retryDocument,
    hasReadyDocuments,
    updateHasReadyDocuments
  };
}
