# Agent Demo 项目骨架

当前工作区已经拆成两个实现目录：

- `frontend/`：基于 `Vue 3 + Vite + TypeScript` 的前端聊天页面骨架
- `python/`：基于 `FastAPI` 的 Python 服务端骨架

当前范围：

- 一个可继续扩展的聊天产品外壳
- 前端本地状态、基础消息列表和输入区
- 后端路由、配置、数据模型和真实 DeepSeek 兼容聊天服务
- 前端已经接入 SSE 流式输出
- 前端已经支持自动滚动、停止生成、基础重试体验
- 为后续工具调用、Agent 编排预留结构

建议的下一步：

1. 明确产品名称和定位文案。
2. 根据你的定位补系统提示词、欢迎语和错误提示文案。
3. 继续完善聊天体验，例如 Markdown 渲染、代码块样式、发送中按钮状态细化。
4. 等本地联调稳定后再补部署文件。

当前开发进度：

1. 前后端基础骨架已搭好。
2. 后端真实 DeepSeek 兼容调用已接通。
3. 前端 SSE 流式输出已接通。
4. 消息区自动滚动、停止生成、基础重试体验已完成。
5. DeepSeek 与 SSE 阅读说明文档已补充。

下一步建议：

1. 给消息内容接 Markdown 渲染。
2. 优化代码块展示和复制体验。
3. 增加“生成中”阶段更细的交互反馈。
4. 如需快速理解接入链路，先阅读 `DEEPSEEK_SSE_READING_GUIDE.md`。

文档维护约定：

1. 当前仓库中的主要源码目录都已补 `README.md`。
2. 以后只要某个目录下的职责、结构、关键逻辑、操作方式发生变化，修改代码时必须同步更新该目录下的 `README.md`。
3. 后续 AI 继续修改本仓库时，必须把“更新对应目录 README”视为同一项工作的一部分，而不是可选项。

本地启动：

```bash
# 前端
cd frontend
npm install
npm run dev
```

```bash
# 后端
cd python
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8001
```
