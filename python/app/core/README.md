# python/app/core 目录说明

## 目录职责

这个目录放服务端基础配置与跨模块共享的底层能力。

## 当前文件

- `config.py`：环境变量读取、默认配置、CORS 来源解析
- `database.py`：SQLite 数据库连接管理、建表逻辑

## 当前关键逻辑

1. 配置只从 `.env` 读取，`.env.example` 只是模板
2. `CORS_ORIGINS` 当前采用逗号分隔字符串解析
3. DeepSeek 相关配置也统一从这里读取
4. 当前本地开发的前端来源按 `5174` 配置
5. `database.py` 使用 `aiosqlite` 管理 SQLite 文件数据库，启用 WAL 模式和外键约束
6. 数据库文件固定落在 `python/agent_demo.db`，避免随启动目录变化而漂移
7. `messages.role` 和 `messages.content` 在建表层增加了基本约束，`conversation_id + sort_order` 增加了唯一索引
8. 数据库在应用启动时通过 `lifespan` 自动初始化建表

## 协作约定

1. 只要配置项、配置来源、默认值或解析方式变化，必须同步更新本文件。
2. 数据库表结构变化时也要同步更新本文件。
