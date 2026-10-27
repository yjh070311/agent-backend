"""创建关闭共享AsyncClient，生命周期在此"""

from contextlib import asynccontextmanager

import httpx2
from fastapi import FastAPI

from app.core.config import get_settings

@asynccontextmanager
async def lifespan(app:FastAPI):
    """
    把http客户端挂载app.state上，供请求复用

    连接池无法复用，每次重新握手，延迟变高
    """

    settings=get_settings()
    app.state.llm_http=httpx2.AsyncClient(
        base_url=settings.llm_base_url.rstrip("/"),
        timeout=httpx2.Timeout(settings.llm_timeout_seconds,connect=10.0),
    )
    try:
        yield
    finally:
        await app.state.llm_http.aclose()