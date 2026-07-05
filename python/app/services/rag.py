"""RAG 检索增强生成服务。"""

import json
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import get_settings
from app.schemas.document import RagChatRequest, RagMode, RagSource
from app.services.llm import LLMService
from app.services.vector_store import SearchResult, VectorStoreService

# RAG 系统提示词模板
RAG_SYSTEM_PROMPT = """你是一个知识库助手。基于以下参考资料回答用户问题。

规则：
1. 优先使用参考资料中的内容
2. 如果参考资料中没有相关信息，说明后基于通用知识回答
3. 引用来源时标注文档名

参考资料：
{context}
"""

# 无检索结果时的回退提示
NO_CONTEXT_PROMPT = """你是一个 AI 助手。请基于你的通用知识回答用户问题。"""


class RAGService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()

    def _should_retrieve(self, rag_mode: RagMode, query: str) -> bool:
        """判断是否需要检索。"""
        if rag_mode == "never":
            return False
        if rag_mode == "always":
            return True
        # auto 模式：简单启发式，短问题或问候语不检索
        greetings = {"你好", "hi", "hello", "嗨", "hey", "你是谁", "你是谁？"}
        if query.strip().lower() in greetings:
            return False
        return True

    def _build_rag_messages(
        self,
        request: RagChatRequest,
        search_results: list[SearchResult],
    ) -> list[dict[str, str]]:
        """构建带参考资料上下文的消息列表。"""
        messages: list[dict[str, str]] = []

        if search_results:
            # 拼接参考资料
            context_parts = []
            for i, result in enumerate(search_results):
                context_parts.append(
                    f"[{i + 1}] 来自《{result.filename}》(片段 {result.chunk_index}):\n{result.snippet}"
                )
            context = "\n\n".join(context_parts)
            system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        else:
            system_prompt = NO_CONTEXT_PROMPT

        messages.append({"role": "system", "content": system_prompt})

        # 添加对话历史
        seen_user_message = False
        for message in request.messages:
            if message.role == "assistant" and not seen_user_message:
                continue
            if message.role == "tool":
                continue
            if message.role == "user":
                seen_user_message = True
            messages.append({"role": message.role, "content": message.content})

        return messages

    def _format_sse(self, event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def rag_chat_stream(
        self,
        request: RagChatRequest,
        user_id: str,
    ) -> AsyncIterator[str]:
        """RAG 流式聊天：检索 + 生成。"""
        # 确保有 API Key
        self.llm_service.ensure_configured()

        # 提取最后一条用户消息作为查询
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            yield self._format_sse("error", {"message": "至少需要一条用户消息。", "status_code": 400})
            yield self._format_sse("done", {"finish_reason": "error"})
            return

        query = user_messages[-1].content
        top_k = request.top_k or self.settings.rag_top_k

        # 决定是否检索
        search_results: list[SearchResult] = []
        if self._should_retrieve(request.rag_mode, query):
            try:
                search_results = await self.vector_store.search(
                    user_id=user_id,
                    query=query,
                    top_k=top_k,
                )
            except Exception:
                # 检索失败不阻塞聊天，降级为普通模式
                search_results = []

        # 构建带上下文的消息
        llm_messages = self._build_rag_messages(request, search_results)

        # 发送 meta 事件，附带检索信息
        meta_data: dict[str, Any] = {
            "mode": "rag",
            "provider": "deepseek",
            "model": self.settings.openai_model,
            "rag_mode": request.rag_mode,
            "sources_count": len(search_results),
        }
        yield self._format_sse("meta", meta_data)

        # 发送 source 事件
        for result in search_results:
            source = RagSource(
                document_id=result.document_id,
                filename=result.filename,
                chunk_index=result.chunk_index,
                snippet=result.snippet[:200],  # 截断过长的片段
            )
            yield self._format_sse("source", source.model_dump())

        # 直接使用 openai SDK 流式调用，复用 LLMService 的客户端
        try:
            stream = await self.llm_service._get_client().chat.completions.create(
                model=self.settings.openai_model,
                messages=llm_messages,
                stream=True,
            )
        except Exception as exc:
            error_msg = "调用模型服务时发生错误。"
            status_code = 502
            if hasattr(exc, "message"):
                error_msg = exc.message
            if hasattr(exc, "status_code"):
                status_code = exc.status_code
            yield self._format_sse("error", {"message": error_msg, "status_code": status_code})
            yield self._format_sse("done", {"finish_reason": "error"})
            return

        finish_reason = "stop"
        has_content = False

        async for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta.content or ""

            if delta:
                has_content = True
                yield self._format_sse("message", {"delta": delta})

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        if not has_content:
            yield self._format_sse("error", {"message": "模型返回了空内容。", "status_code": 502})
            yield self._format_sse("done", {"finish_reason": "error"})
            return

        yield self._format_sse("done", {"finish_reason": finish_reason})
