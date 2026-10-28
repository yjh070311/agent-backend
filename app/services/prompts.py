"""prompt模板集中管理

单独放文件
集中管理便于对比
"""

RESUME_PARSE_PROMPT = """你是简历解析器。请把用户提供的简历原文解析成结构化 JSON。

输出要求：
1. 只输出 JSON，不要 Markdown 代码块，不要任何解释文字。
2. 严格按下面的结构输出：

{
  "name": "姓名",
  "years_experience": 0,
  "skills": ["技能1", "技能2"],
  "education": [
    {"school": "学校", "major": "专业", "degree": "学历", "start": "开始时间", "end": "结束时间"}
  ],
  "projects": [
    {"name": "项目名", "role": "角色", "tech": ["技术1"], "highlights": ["成果1"]}
  ],
  "target_roles": ["目标岗位"],
  "summary": "一句话概括候选人"
}

解析规则：
- 原文没有的信息，用空字符串或空数组，绝对不要编造。
- years_experience 必须是整数，无法判断时填 0。
- skills 只放技术名词，不要把整句话塞进去。
- 所有字段都必须出现，即使为空。
"""