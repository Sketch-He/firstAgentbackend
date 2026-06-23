from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LLMService


class AgentService:
    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService()

    async def run(self, request: ChatRequest) -> ChatResponse:
        return await self.llm_service.generate_reply(request)
