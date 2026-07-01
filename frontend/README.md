# frontend 目录说明

## 目录职责

这个目录承载前端应用，技术栈为 `Vue 3 + Vite + TypeScript`。当前推荐部署目标是 `Railway`。

## 当前包含内容

- 基础页面壳
- 聊天消息列表与输入区
- 前端本地会话状态
- 基于 SSE 的流式对话接收逻辑
- 消息自动滚动到底部
- 停止生成与重试体验
- 基础 Markdown 消息渲染
- 代码块展示与复制
- 更细的生成阶段提示
- 桌面端采用“浏览器窗口滚动消息内容 + 左侧 Sidebar 独立滚动 + 底部输入区固定”的布局

## 当前部署状态

1. 前端已经可以通过 `VITE_API_BASE_URL` 指向独立后端域名。
2. 本地开发默认仍走 Vite 代理，代理目标是 `127.0.0.1:8001`。
3. `frontend/.env.example` 已补齐本地直连示例和生产示例。
4. 生产环境通过 `server.mjs` 提供静态文件服务和 SPA 路由回退，直接适配 Railway 注入的 `PORT`。

## 现在要做什么

1. 在 Railway 新建一个前端服务。
2. 把服务根目录设置为 `frontend/`。
3. 在 Railway 配置环境变量 `VITE_API_BASE_URL=https://<your-backend-domain>`。
4. 触发部署，确认 Railway 完成 `npm run build` 并通过 `npm start` 启动前端服务。
5. 打开 Railway 分配的公开域名，确认首页和 `/health` 可访问。

## 接下来要做什么

1. 等 Railway 前后端域名都稳定后，再绑定正式前端域名。
2. 如果未来接入登录态、埋点或监控，再按 Railway 环境分组补更多环境变量。
3. 如果未来出现 SSR、边缘逻辑或全球加速诉求，再评估是否切换到更适合前端分发的平台。

## 常用操作

```bash
npm install
npm run dev
npm run build
npm start
```

## 协作约定

1. 只要这个目录下的结构、职责、启动方式、状态流、接口调用方式发生变化，必须同步更新本文档。
2. 后续 AI 在修改 `src/` 下的模块边界、状态管理方式、流式交互协议时，也必须同时检查并更新本文档。
3. 如果新增重要子目录，也要补对应的 `README.md`。
