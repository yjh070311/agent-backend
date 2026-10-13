"""FastAPI 应用入口。

启动方式（必须在项目根目录执行）：
    .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.core.logging_config import setup_logging
from app.core.middleware import register_middleware
from app.routers import chat, conversations, health, messages
from app.utils.errors import register_exception_handler

# 必须最先执行，否则启动阶段的日志没有格式
setup_logging()

app = FastAPI(
    title="Agent Backend",
    description="AI Agent 后端服务骨架",
    version="0.2.0",
)

register_middleware(app)
register_exception_handler(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(messages.router)


@app.get("/")
async def root() -> dict[str, str]:
    """根路由：返回欢迎信息，指向接口文档。"""
    return {"message": "Agent Backend 已启动，访问 /docs 查看接口文档"}


@app.get("/boom")
async def boom() -> dict[str, str]:
    """临时接口：故意制造未处理异常，用来验证兜底处理器。验证完请删掉。"""
    raise RuntimeError("这是用于验证 500 兜底处理器的故意异常")