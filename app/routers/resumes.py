"""简历接口"""

import httpx2
from fastapi import APIRouter, Depends

from app.models import User
from app.schemas.resume import ParseTextRequest, ResumeProfile
from app.services.llm_client import get_llm_http
from app.services.resume_parser import parse_resume_text
from app.utils.deps import get_current_user
from app.utils.response import ApiResponse

router = APIRouter(prefix="/resume", tags=["简历"])


@router.post("/parse", response_model=ApiResponse[ResumeProfile])
async def parse_resume(
    payload: ParseTextRequest,
    http: httpx2.AsyncClient = Depends(get_llm_http),
    user: User = Depends(get_current_user),
) -> ApiResponse[ResumeProfile]:
    """把简历纯文本解析成结构化画像。

    v1 先只收文本：把「解析质量」这件事单独验证清楚，
    PDF/Word 上传放到下一步，避免一开始就被文件格式淹没。
    """
    profile = await parse_resume_text(http, payload.text)
    return ApiResponse.success(data=profile)
