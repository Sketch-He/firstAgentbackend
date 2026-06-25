from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorCode:
    """业务错误码常量。code=0 表示成功，非 0 表示失败。"""

    SUCCESS = 0

    # 通用错误
    NOT_FOUND = 10001
    BAD_REQUEST = 10002
    CONFLICT = 10003

    # LLM 服务错误
    LLM_CONFIG_ERROR = 20001
    LLM_RATE_LIMIT = 20002
    LLM_CONNECTION_ERROR = 20003
    LLM_SERVICE_ERROR = 20004

    # 未知错误
    UNKNOWN = 99999


# HTTP 状态码到业务错误码的默认映射。
HTTP_STATUS_TO_CODE: dict[int, int] = {
    400: ErrorCode.BAD_REQUEST,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    429: ErrorCode.LLM_RATE_LIMIT,
    500: ErrorCode.LLM_CONFIG_ERROR,
    502: ErrorCode.LLM_CONNECTION_ERROR,
}


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应包装。"""

    code: int = Field(default=ErrorCode.SUCCESS, description="业务状态码，0 表示成功")
    message: str = Field(default="ok", description="人类可读的提示信息")
    data: T | None = Field(default=None, description="业务数据")

    @classmethod
    def success(cls, data: Any = None, message: str = "ok") -> "ApiResponse":
        return cls(code=ErrorCode.SUCCESS, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "ApiResponse":
        return cls(code=code, message=message, data=None)
