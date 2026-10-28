"""岗位匹配路由（v0：技能集合打分）。"""

from fastapi import APIRouter, Depends

from app.models import User
from app.schemas.match import SkillMatchRequest, SkillMatchResult
from app.services.similarity import skill_match
from app.utils.deps import get_current_user
from app.utils.response import ApiResponse

router = APIRouter(prefix="/match", tags=["岗位匹配"])


@router.post("/skills", response_model=ApiResponse[SkillMatchResult])
async def match_skills(
    payload: SkillMatchRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[SkillMatchResult]:
    """输入两组技能，返回匹配度、命中项、缺失项。

    分数由代码算，不由模型给——这是可复现、可解释的前提。
    """
    result = skill_match(payload.resume_skills, payload.job_skills)
    return ApiResponse.success(data=SkillMatchResult(**result))