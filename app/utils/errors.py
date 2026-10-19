"""统一异常定义与全局异常处理器。"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.response import ApiResponse

logger = logging.getLogger("agent_backend")


class BusinessException(Exception):
    """业务异常：同时携带业务错误码和 HTTP 状态码。"""

    def __init__(
        self,
        code: int,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundException(BusinessException):
    """资源不存在。越权也走这里，统一 404，避免泄露资源是否存在。"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(code=40402, message=message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(BusinessException):
    """未认证或凭证无效。错误码尾号 01 表示认证类。"""

    def __init__(self, message: str = "未认证，请先登录") -> None:
        super().__init__(code=40101, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ConflictException(BusinessException):
    """资源冲突，例如用户名已被注册。"""

    def __init__(self, message: str = "资源已存在") -> None:
        super().__init__(code=40901, message=message, status_code=status.HTTP_409_CONFLICT)


def register_exception_handler(app: FastAPI) -> None:
    """注册全局异常处理器，在 main.py 里调用一次即可。"""

    @app.exception_handler(BusinessException)
    async def handle_business_error(request: Request, exc: BusinessException) -> JSONResponse:
        logger.warning("业务异常 code=%s %s %s", exc.code, request.method, request.url.path)
        body = ApiResponse.error(code=exc.code, message=exc.message).model_dump()
        return JSONResponse(content=body, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in error.get("loc", ()))
        detail = f"{location}: {error.get('msg', '请求参数不合法')}"
        logger.info("参数异常 %s %s %s", request.method, request.url.path, detail)
        body = ApiResponse.error(code=42200, message=detail).model_dump()
        return JSONResponse(content=body, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.info("http 错误 %s %s -> %s", exc.status_code, request.method, request.url.path)
        body = ApiResponse.error(code=exc.status_code * 100, message=str(exc.detail)).model_dump()
        return JSONResponse(content=body, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        logger.exception("未处理异常 request_id=%s %s %s", request_id, request.method, request.url.path)
        body = ApiResponse.error(
            code=50000,
            message="服务器内部错误，请把响应头里的 X-Request-ID 提供给管理员",
        ).model_dump()
        return JSONResponse(
            content=body,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # 修改点：头名必须是连字符 X-Request-ID。
            # 写成 X_Request_ID 会让上面那句「请提供 X-Request-ID」失效。
            headers={"X-Request-ID": request_id},
        )