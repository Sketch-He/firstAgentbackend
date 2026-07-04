# 登录系统设计方案

## 当前状态

- 使用随机 user_id 存 cookie，无真实用户账号
- 所有请求通过 `X-User-Id` header 传递用户标识
- conversations 表已有 `user_id` 字段

## 改造方案

### 方案 A：简单邀请码

适合小范围使用，无需真实账号系统。

**实现：**
1. 环境变量配置 `ACCESS_CODE`
2. 前端首次访问弹窗输入邀请码
3. 验证通过后生成 token 存 localStorage
4. 后端中间件校验 token

**改动量：** 小（1-2天）

---

### 方案 B：OAuth 登录（GitHub/Google）

适合公开项目，用户用第三方账号登录。

**实现：**
1. 后端接入 OAuth2 流程（推荐 `authlib` 库）
2. 前端跳转授权页，回调后获取 token
3. 后端创建/关联 users 表
4. conversations.user_id 关联真实用户

**新增依赖：**
- `authlib`（OAuth 客户端）
- `python-jose`（JWT 处理）

**改动量：** 中（3-5天）

---

### 方案 C：邮箱验证码

适合不想依赖第三方的场景。

**实现：**
1. 用户输入邮箱，后端发送验证码（SMTP 或第三方邮件服务）
2. 验证通过后创建账号，返回 token
3. 后续用 token 认证

**新增依赖：**
- 邮件服务（SendGrid / Resend / 自建 SMTP）

**改动量：** 中（3-5天）

---

## 技术改造点

### 后端

1. **新增 users 表**（如需要）
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    created_at TEXT NOT NULL
);
```

2. **认证中间件**
- 从 `Authorization: Bearer <token>` 解析 user_id
- 替换现在从 `X-User-Id` header 读取的逻辑

3. **新增路由**
- `POST /api/auth/login` - 登录
- `POST /api/auth/logout` - 登出
- `GET /api/auth/me` - 获取当前用户

### 前端

1. **登录页面/弹窗**
2. **token 管理**（localStorage）
3. **请求拦截器**（自动带 Authorization header）
4. **路由守卫**（未登录跳转登录页）

### 数据迁移

- 现有数据的 `user_id` 为空字符串
- 需要脚本将匿名数据关联到首个登录用户，或清理

---

## 推荐路径

1. 先用**方案 A（邀请码）**快速保护访问
2. 后续需要多用户时再做**方案 B（OAuth）**

---

*最后更新：2026-07-04*
