# frontend/src 目录说明

## 目录职责

`src/` 存放前端核心源码，是页面、组件、状态、接口封装和样式的主入口。

## 当前结构

- `components/`: 通用界面组件
- `composables/`: 组合式状态与业务逻辑
- `lib/`: 接口调用与底层工具封装
- `pages/`: 页面级组件
- `styles/`: 全局样式
- `types/`: 共享类型定义

## 当前关键逻辑

1. 页面主入口在 `App.vue` 和 `pages/ChatPage.vue`
2. 聊天状态集中在 `composables/useChat.ts`
3. HTTP 与 SSE 请求封装在 `lib/chatApi.ts`
4. 消息 Markdown 解析工具在 `lib/markdown.ts`
5. 桌面端当前采用”浏览器窗口滚动消息内容 + Sidebar 独立滚动 + Header/Composer 粘住视口”的聊天布局
6. 文档管理状态集中在 `composables/useDocuments.ts`
7. RAG 来源引用通过 `messageSources` 跟踪，由 `SourceBubble` 组件展示

## 协作约定

1. 只要 `src/` 下的目录划分、核心状态流、页面入口、接口组织方式变化，必须同步更新本文档。
2. 后续 AI 在新增新的核心模块时，需要先判断是否应该补对应子目录 `README.md`。
