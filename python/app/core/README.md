# python/app/core 目录说明

## 目录职责

这个目录存放服务端基础配置与跨模块共享的底层能力。

## 当前文件

- `config.py`：环境变量读取、默认配置、CORS 来源解析、SQLite 路径解析
- `database.py`：SQLite 连接管理、路径解析、建表逻辑
- `exceptions.py`：业务异常类 `ApiError` 和全局异常处理器注册

## 当前关键逻辑

1. 配置只从 `.env` 读取，`.env.example` 只是模板。
2. `CORS_ORIGINS_RAW` 采用逗号分隔字符串解析，便于同时配置本地和生产前端来源。
3. `SQLITE_PATH` 支持两种写法：
   相对路径：自动解析到 `python/` 目录下。
   绝对路径：直接使用，适合 Railway volume，例如 `/data/agent_demo.db`。
4. `database.py` 使用 `aiosqlite` 管理 SQLite 文件数据库，启用 WAL 模式和外键约束。
5. 数据库目录会在启动时自动创建，避免部署时因为挂载目录不存在而启动失败。
6. `messages.role` 和 `messages.content` 在建表层增加了基本约束，`conversation_id + sort_order` 增加了唯一索引。
7. 数据库在应用启动时通过 `lifespan` 自动初始化建表。
8. `exceptions.py` 统一把错误收口成 `{ code, message, data }` 返回格式。

## 现在要做什么

1. 在 Railway 把 `CORS_ORIGINS_RAW` 配成真实前端域名，可以是 Railway 域名或自定义域名。
2. 在 Railway 把 `SQLITE_PATH` 配成挂载 volume 内的绝对路径。
3. 上线后确认 `/health`、会话列表和流式聊天都能正确访问数据库文件。

## 接下来要做什么

1. 未来切换到 `Postgres` 时，需要重做这里的数据库连接和初始化逻辑。
2. 如果引入多环境配置策略，也需要在这里统一整理环境变量来源和解析方式。

## 协作约定

1. 只要配置项、配置来源、默认值或解析方式变化，必须同步更新本文件。
2. 数据库表结构变化时，也要同步更新本文件。
