"""简历文本-》结构化画像"""
import json
from typing import Any

import httpx2
from pydantic import ValidationError

from app.schemas.resume import ResumeProfile
from app.services.llm_client import chat_once
from app.services.prompts import RESUME_PARSE_PROMPT
from app.utils.errors import BusinessException


class ResumeParseError(BusinessException):
    """简历解析失败——模型给的输出无法变成结构化对象。"""

    def __init__(self, message: str) -> None:
        super().__init__(code=42210, message=message, status_code=422)


def strip_code_fences(text: str) -> str:
    """去掉模型偶尔加的 ```json ... ``` 包裹。

    模型即使被要求"只输出 JSON"，也经常加代码块。
    这不是理论问题——真实调用里很常见。
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


async def parse_resume_text(
    http: httpx2.AsyncClient,
    text: str,
    *,
    max_attempts: int = 2,
) -> ResumeProfile:
    """把简历原文解析成 ResumeProfile。

    失败处理分两层：
        1. 解析失败/校验失败 → 把错误原因反馈给模型，重试一次；
        2. 重试仍失败 → 抛 422 业务异常，不返回 500，也不吞掉错误。
    """
    if not text.strip():
        raise ResumeParseError("简历内容为空")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": RESUME_PARSE_PROMPT},
        {"role": "user", "content": text[:12000]},
    ]
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        result = await chat_once(
            http,
            messages,
            temperature=0.0,  # 解析任务要稳定，不要创造性
            max_tokens=2048,
        )
        raw = result["content"]

        try:
            data: Any = json.loads(strip_code_fences(raw))
            return ResumeProfile.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:200]
            if attempt >= max_attempts:
                break
            # 把模型的坏输出和错误原因一起带回去，让它自我修正
            messages = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        f"上面的输出无法解析：{last_error}。"
                        "请只输出符合结构的 JSON，不要任何其他文字。"
                    ),
                },
            ]

    raise ResumeParseError(f"简历解析失败：{last_error}")