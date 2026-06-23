# frontend/src 目录说明

## 目录职责

`src/` 存放前端核心源码，是页面、组件、状态、接口封装和样式的主入口。

## 当前结构

- `components/`：通用界面组件
- `composables/`：组合式状态与业务逻辑
- `lib/`：接口调用与底层工具封装
- `pages/`：页面级组件
- `styles/`：全局样式
- `types/`：共享类型定义

## 当前关键逻辑

1. 页面主入口在 `App.vue` 和 `pages/ChatPage.vue`
2. 聊天状态集中在 `composables/useChat.ts`
3. 服务探活逻辑在 `composables/useServiceHealth.ts`
4. HTTP 与 SSE 请求封装在 `lib/chatApi.ts`

## 协作约定

1. 只要 `src/` 下的目录划分、核心状态流、页面入口、接口组织方式变化，必须同步更新本文件。
2. 后续 AI 在新增新的核心模块时，需要先判断是否应新增子目录 README。
