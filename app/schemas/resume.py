"""
简历解析几位勾画模型

方便后面岗位匹配比对
"""

from pydantic import BaseModel, ConfigDict, Field


class EducationItem(BaseModel):
    """一段教育经历。"""

    model_config = ConfigDict(extra="ignore")

    school: str = Field(default="", description="学校名")
    major: str = Field(default="", description="专业")
    degree: str = Field(default="", description="学历，如本科/硕士")
    start: str = Field(default="", description="开始时间")
    end: str = Field(default="", description="结束时间")


class ProjectItem(BaseModel):
    """一段项目经历。"""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(default="", description="项目名")
    role: str = Field(default="", description="担任角色")
    tech: list[str] = Field(default_factory=list, description="技术栈")
    highlights: list[str] = Field(default_factory=list, description="亮点或成果")


class ResumeProfile(BaseModel):
    """候选人画像——简历解析的唯一输出结构。"""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(default="", description="姓名")
    years_experience: int = Field(default=0, ge=0, le=50, description="工作/实习年限")
    skills: list[str] = Field(default_factory=list, description="技能关键词")
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list, description="求职意向")
    summary: str = Field(default="", description="一句话概括")


class ParseTextRequest(BaseModel):
    """简历解析请求体（v1 先收纯文本，PDF 上传放到下一步）。"""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        min_length=10,
        max_length=20000,
        description="简历原文，至少 10 个字符",
    )