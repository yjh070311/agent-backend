"""LLM诊断路由"""

import httpx2
from fastapi import APIRouter,Depends

from app.models import User
from app.schemas.llm import PingRequest, PingResponse
from app.services.llm_client import chat_once, get_llm_http
from app.utils.deps import get_current_user
from app.utils.response import ApiResponse


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