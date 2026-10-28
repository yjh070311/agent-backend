"""技能匹配打分 v0：用集合重合算分。

为什么不让模型直接给分：
    同一份简历两次可能给 70 和 85，不可复现、也无法解释。
    这里由代码算：命中数 / 必需技能数 × 100。

v1（W2）：把集合重合换成 embedding 余弦相似度，接口和返回结构不变。
"""

from app.utils.errors import BusinessException


def normalize(skills: list[str]) -> set[str]:
    """统一大小写和空白，避免 "Python" 和 " python " 被当成两个技能。"""
    return {skill.strip().lower() for skill in skills if skill.strip()}


def skill_match(resume_skills: list[str], job_skills: list[str]) -> dict:
    """计算技能匹配度。

    返回 score(0-100) / matched / missing，后两者保留 JD 原始写法。
    """
    required = normalize(job_skills)
    if not required:
        raise BusinessException(code=40005, message="岗位技能列表不能为空")

    owned = normalize(resume_skills)
    matched: list[str] = []
    missing: list[str] = []
    for skill in job_skills:
        if skill.strip().lower() in owned:
            matched.append(skill)
        else:
            missing.append(skill)

    score = round(len(matched) / len(required) * 100)
    return {"score": score, "matched": matched, "missing": missing}