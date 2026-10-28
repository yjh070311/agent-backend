"""LLM诊断路由"""

import httpx2
from fastapi import APIRouter,Depends

from app.models import User
from app.schemas.llm import PingRequest, PingResponse
from app.services.llm_client import chat_once, get_llm_http
from app.utils.deps import get_current_user
from app.utils.response import ApiResponse

import json

from fastapi.responses import StreamingResponse

from app.services.llm_client import chat_stream
from app.utils.errors import BusinessException

router=APIRouter(prefix="/llm",tags=["LLM"])


@router.post("/ping",response_model=ApiResponse[PingResponse])
async def ping(
    payload:PingRequest,
    http:httpx2.AsyncClient=Depends(get_llm_http),
    user:User=Depends(get_current_user),
) -> ApiResponse[PingResponse]:
    result=await chat_once(
        http,
        [{"role":"user","content":payload.prompt}],
        max_tokens=128,
    )
    return ApiResponse.success(data=PingResponse(**result))


@router.post("/stream")
async def stream_chat(
    payload: PingRequest,
    http: httpx2.AsyncClient = Depends(get_llm_http),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """流式版本：逐字返回模型输出。

    一旦开始返回 200，就没法再改成 4xx/5xx，
    流式中的错误只能作为一条 SSE 事件发出去。
    """

    async def event_source():
        try:
            async for delta in chat_stream(
                http,
                [{"role": "user", "content": payload.prompt}],
                max_tokens=256,
            ):
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except BusinessException as exc:
            yield (
                "data: "
                + json.dumps({"error": exc.message, "code": exc.code}, ensure_ascii=False)
                + "\n\n"
            )
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
