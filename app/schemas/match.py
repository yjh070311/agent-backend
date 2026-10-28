"""技能匹配接口的请求与响应模型。"""

from pydantic import BaseModel, ConfigDict, Field


class SkillMatchRequest(BaseModel):
    """输入：候选人技能 + 岗位要求技能。"""

    model_config = ConfigDict(extra="forbid")

    resume_skills: list[str] = Field(default_factory=list, description="简历里的技能")
    job_skills: list[str] = Field(min_length=1, description="岗位必需技能")


class SkillMatchResult(BaseModel):
    """输出：分数 + 命中 + 缺失。"""

    score: int
    matched: list[str]
    missing: list[str]