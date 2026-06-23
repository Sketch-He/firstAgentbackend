import { onMounted, ref } from "vue";
import { fetchHealth } from "../lib/chatApi";

export type ServiceStatus = "checking" | "online" | "offline";

export function useServiceHealth() {
  const status = ref<ServiceStatus>("checking");
  const serviceName = ref("后端服务");

  async function checkHealth() {
    status.value = "checking";

    try {
      const response = await fetchHealth();

      status.value = response.status === "ok" ? "online" : "offline";
      serviceName.value = response.service;
    } catch {
      status.value = "offline";
    }
  }

  // 页面初始化时先做一次探活，后续如果要自动轮询可以直接在这里扩展。
  onMounted(() => {
    void checkHealth();
  });

  return {
    checkHealth,
    serviceName,
    status
  };
}
