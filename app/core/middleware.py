"""请求上下文中间件--请求追踪
生成request_id记录请求
"""

import logging
import uuid
import time
from fastapi import FastAPI,Request

logger=logging.getLogger("agent_backend.access")

def register_middleware(app:FastAPI):
    @app.middleware("http")
    async def middleware(request:Request,call_next):
        request_id=uuid.uuid4().hex[:8]
        request.state.request_id=request_id

        start=time.perf_counter()

        response=await call_next(request)

        cost_time=(time.perf_counter()-start)*1000

        response.headers["X-Request-ID"]=request_id

        logger.info("%s %s ->%s %.1fms request_id=%s",request.method,request.url.path,response.status_code,cost_time,request_id
        )
        return response
