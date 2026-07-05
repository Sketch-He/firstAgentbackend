# CLAUDE.md — 项目开发规范

> 本文件是 AI 助手在本仓库中工作的全局规范。每次修改代码前必须阅读并遵守。

## 核心原则

1. **先读再改**：修改任何文件前，必须先读取该文件的完整内容
2. **改完必测**：代码修改后必须运行相关测试，确认无回归
3. **边界覆盖**：必须考虑成功、失败、边界三种情况
4. **文档同步**：代码变更必须同步更新对应的 README.md

## 开发流程检查清单

每次完成任务前，必须逐项确认：

### 代码质量
- [ ] 所有新增/修改的函数都有明确的错误处理
- [ ] 后台任务（asyncio.create_task）的异常不会静默丢失
- [ ] 文件操作有 try/except 保护
- [ ] 数据库操作在 finally 块中关闭连接
- [ ] 前端异步操作有 loading/error 状态管理

### 业务场景
- [ ] 考虑了用户中途取消/断开连接的情况
- [ ] 考虑了重复提交的幂等性
- [ ] 考虑了资源清理（临时文件、向量数据等）
- [ ] 考虑了并发访问的安全性
- [ ] 考虑了大数据量下的性能

### 测试验证
- [ ] 后端改动：运行 `cd python && .venv/Scripts/pytest`
- [ ] 前端改动：运行 `cd frontend && npm run test`
- [ ] 手动测试核心流程（上传→处理→检索→问答）
- [ ] 检查浏览器控制台和后端日志无报错

### 文档更新
- [ ] 修改了目录结构：更新对应目录的 README.md
- [ ] 修改了 API：更新 docs/project-guide.md 的 API 章节
- [ ] 修改了技术选型：更新 docs/project-guide.md 的技术选型章节
- [ ] 新增/修改了环境变量：更新 .env.example 和 docs/project-guide.md

## 后端开发规范

### 错误处理模式

```python
# ✅ 正确：后台任务必须捕获所有异常并记录
async def _background_task(doc_id: str):
    try:
        # 业务逻辑
        await do_work()
        await update_status(doc_id, "ready")
    except Exception as exc:
        # 必须记录失败状态，不能静默吞掉
        await update_status(doc_id, "failed", error_message=str(exc))

# ❌ 错误：异常被静默吞掉
async def _background_task(doc_id: str):
    try:
        await do_work()
    except Exception:
        pass  # 这会导致状态永远卡在 processing
```

### 资源清理模式

```python
# ✅ 正确：持久化文件在删除时清理
async def delete_resource(id: str):
    # 1. 清理关联数据
    try:
        vector_store.delete(id)
    except Exception:
        pass  # 关联清理失败不阻塞主流程

    # 2. 清理文件
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass

    # 3. 清理数据库记录
    await delete_record(id)
```

### 数据库操作模式

```python
# ✅ 正确：使用 try/finally 确保连接关闭
async def get_data():
    db = await get_db()
    try:
        cursor = await db.execute("SELECT ...")
        return await cursor.fetchall()
    finally:
        await db.close()
```

## 前端开发规范

### 状态管理模式

```typescript
// ✅ 正确：完整的 loading/error/data 状态
const isLoading = ref(false);
const error = ref<string | null>(null);
const data = ref<T[]>([]);

async function fetchData() {
  isLoading.value = true;
  error.value = null;
  try {
    data.value = await apiCall();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "操作失败";
  } finally {
    isLoading.value = false;
  }
}
```

### 轮询模式

```typescript
// ✅ 正确：有停止条件的轮询
let timer: ReturnType<typeof setInterval> | null = null;

function startPolling(ids: Set<string>) {
  if (timer !== null) return;
  timer = setInterval(async () => {
    for (const id of ids) {
      const result = await checkStatus(id);
      if (result.status !== "processing") {
        ids.delete(id);
      }
    }
    if (ids.size === 0) {
      clearInterval(timer);
      timer = null;
    }
  }, 2000);
}
```

## 测试规范

### 后端测试

```python
# 测试文件位置：python/tests/
# 运行方式：cd python && .venv/Scripts/pytest

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

async def test_upload_document(client):
    # 测试上传流程
    ...

async def test_upload_invalid_file(client):
    # 测试错误场景
    ...
```

### 前端测试

```typescript
// 测试文件位置：frontend/src/__tests__/
// 运行方式：cd frontend && npm run test

import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import MyComponent from "../components/MyComponent.vue";

describe("MyComponent", () => {
  it("renders correctly", () => {
    const wrapper = mount(MyComponent);
    expect(wrapper.exists()).toBe(true);
  });

  it("handles error state", async () => {
    // 测试错误状态
  });
});
```

## 常见 Bug 预防

### 1. 后台任务静默失败

**问题**：`asyncio.create_task` 中的异常不会传播到调用方
**解决**：在任务内部捕获所有异常，更新状态为 failed

### 2. 临时文件未清理

**问题**：使用 tempfile 后忘记清理，或清理时机不对
**解决**：使用持久化目录，在删除资源时统一清理

### 3. 前端状态不同步

**问题**：异步操作完成后 UI 未更新
**解决**：使用轮询或 WebSocket 确保状态同步

### 4. 重复提交

**问题**：用户快速点击导致重复请求
**解决**：使用 loading 状态禁用按钮，或使用防抖

---

*最后更新：2026-07-05*
