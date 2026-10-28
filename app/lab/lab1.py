"""Lab 01：结构化输出 + 校验重试最小验证（不需要 API key）。

是什么：让“模型”输出 JSON，用 Pydantic 校验；坏了就把错误反馈回去重试一次。
跑出什么：第 1 次输出带 Markdown 代码块 → 第 2 次修正 → 解析成功。

直接运行：
    python labs/lab01_structured_output.py

故意改坏：把 max_attempts 改成 1，观察它是不是直接抛异常。
"""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ResumeProfile(BaseModel):
    """只保留最关键的三个字段，方便观察。"""

    name: str = Field(default="")
    skills: list[str] = Field(default_factory=list)
    years_experience: int = Field(default=0, ge=0, le=50)


# 模拟模型：第 1 次故意给一个带代码块、且 years_experience 是字符串的坏输出
FAKE_LLM_OUTPUTS = [
    '```json\n{"name": "张三", "skills": "Python, FastAPI", "years_experience": "一年"}\n```',
    '{"name": "张三", "skills": ["Python", "FastAPI"], "years_experience": 1}',
]


def fake_llm_call(messages: list[dict[str, str]]) -> str:
    """用列表轮换取代表“模型第几次回答”。"""
    index = min(len([m for m in messages if m["role"] == "assistant"]), len(FAKE_LLM_OUTPUTS) - 1)
    return FAKE_LLM_OUTPUTS[index]


def strip_code_fences(text: str) -> str:
    """去掉 ```json ... ``` 包裹。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def parse_with_retry(
    text: str,
    *,
    max_attempts: int = 2,
) -> ResumeProfile:
    """解析 + 校验 + 失败反馈重试。"""
    messages: list[dict[str, str]] = [{"role": "user", "content": text}]
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        raw = fake_llm_call(messages)
        print(f"第 {attempt} 次模型输出：{raw[:70]}")

        try:
            data: Any = json.loads(strip_code_fences(raw))
            profile = ResumeProfile.model_validate(data)
            print(f"第 {attempt} 次解析成功：{profile}")
            return profile
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:120]
            print(f"第 {attempt} 次解析失败：{last_error}")
            if attempt >= max_attempts:
                break
            # 关键：把坏输出和错误原因一起反馈给模型
            messages = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"上面的输出无法解析：{last_error}。请只输出合法 JSON。",
                },
            ]

    raise ValueError(f"解析失败：{last_error}")


if __name__ == "__main__":
    profile = parse_with_retry("张三，会 Python 和 FastAPI，一年经验。")
    print()
    print("最终结果：")
    print(json.dumps(profile.model_dump(), ensure_ascii=False, indent=2))
