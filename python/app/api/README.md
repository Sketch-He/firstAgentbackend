# python/app/api 目录说明

## 目录职责

这个目录负责 HTTP 接口层，处理路由注册、请求进入和响应返回。

## 当前结构

- `router.py`：API 路由聚合入口（chat、conversations、documents）
- `routes/`：具体路由模块

## 协作约定

1. 如果新增新的 API 域，例如 `users`、`files`、`tools`，必须同步更新本文件。
2. 路由前缀或聚合方式变化时，也要更新本文件。
