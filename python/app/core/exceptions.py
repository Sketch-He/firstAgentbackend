from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.response import ApiResponse, ErrorCode, HTTP_STATUS_TO_CODE


class ApiError(Exception):
    """业务异常，携带业务错误码和提示信息。"""

    def __init__(self, code: int, message: str, status_code: int = 200) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，确保所有错误都以统一格式返回。"""

    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = " -> ".join(str(item) for item in first_error.get("loc", []))
        msg = first_error.get("message", "请求参数校验失败。")
        detail = f"{loc}: {msg}" if loc else msg

        return JSONResponse(
            status_code=422,
            content=ApiResponse.error(
                code=ErrorCode.BAD_REQUEST, message=f"请求参数错误：{detail}"
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(
                code=ErrorCode.UNKNOWN, message="服务器内部错误，请稍后重试。"
            ).model_dump(),
        )
