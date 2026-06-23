import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const backendTarget = "http://127.0.0.1:8001";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      "/api": backendTarget,
      "/health": backendTarget
    }
  },
  preview: {
    port: 4173
  }
});
