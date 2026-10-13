from fastapi import FastAPI,status,Request
import logging
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.response import ApiResponse



class BusinessException(Exception):
    def __init__(self,
                code:int,
                message:str,
                status_code:int=status.HTTP_400_BAD_REQUEST,
                )->None:
        super().__init__(message)
        self.code=code
        self.message=message
        self.status_code=status_code

class NotFoundException(BusinessException):
    def __init__(self, message:str="不存在"):
        super().__init__(code=40401, message=message, status_code=status.HTTP_404_NOT_FOUND)



logger=logging.getLogger("agent_backend")

def register_exception_handler(app:FastAPI)->None:

    @app.exception_handler(BusinessException)
    async def handle_business_error(request:Request,exc:BusinessException)->JSONResponse:
        logger.warning("业务异常 code=%s %s %s",exc.code,request.method,request.url.path)
        body=ApiResponse.error(code=exc.code,message=exc.message).model_dump()

        return JSONResponse(content=body,status_code=exc.status_code)
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request:Request,exc:RequestValidationError)->JSONResponse:
        error=exc.errors()[0] if exc.errors() else {}
        location=".".join(str(part) for part in error.get("loc",()))
        detail=f"{location}:{error.get('msg','请求参数不合法')}"
        logger.info("参数异常 %s %s %s",request.method,request.url.path,detail)
        body=ApiResponse.error(code=42200,message=detail).model_dump()
        return JSONResponse(content=body,status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)



    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request:Request,exc:StarletteHTTPException)->JSONResponse:
        logger.info("http错误 %s %s->%s",exc.status_code,request.method,request.url.path)
        body=ApiResponse.error(code=exc.status_code*100,message=str(exc.detail)).model_dump()

        return JSONResponse(content=body,status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request:Request,exc:Exception)->JSONResponse:
        request_id=getattr(request.state,"request_id","-")
        body=ApiResponse.error(code=50000,message="服务器内部错误，请把响应头里的 X-Request-ID 提供给管理员").model_dump()
        logger.exception("其他错误 %s %s %s",request_id,request.method,request.url.path)

        return JSONResponse(content=body,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,headers={"X-Request-ID":request_id})
