from fastapi import APIRouter

from app.schemas.chat import HealthResponse
from app.schemas.response import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> ApiResponse[HealthResponse]:
    return ApiResponse.success(data=HealthResponse(status="ok", service="python-api"))
