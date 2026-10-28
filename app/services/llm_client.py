"""LLM 调用封装：构建请求、解析响应、把失败翻译成项目异常。"""

from typing import Any

import json
import httpx2
from fastapi import Request

from app.core.config import get_settings
from app.utils.errors import BusinessException


class LLMServiceError(BusinessException):
    """上游 LLM 服务出错（502），和「我们自己的代码出错（500）」区分开。"""

    def __init__(self, message: str, code: int = 50201) -> None:
        super().__init__(code=code, message=message, status_code=502)


class LLMTimeoutError(LLMServiceError):
    """LLM 超时（504）。"""

    def __init__(self, message: str = "LLM 响应超时") -> None:
        super().__init__(message, code=50401)


def _usage_from(body: dict[str, Any]) -> dict[str, int]:
    """从响应里提取 token 用量；缺失时返回 0 而不是崩掉。"""
    usage = body.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


async def chat_once(
    http: httpx2.AsyncClient,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """发一次对话请求，返回 {content, usage, model}。

    http 由调用方传入，测试时可以换成 MockTransport 的客户端，不联网。
    """
    settings = get_settings()
    if not settings.llm_api_key:
        raise BusinessException(
            code=50002,
            message="未配置 LLM_API_KEY，请在 .env 里填写",
            status_code=500,
        )

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = await http.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
    except httpx2.TimeoutException as exc:
        raise LLMTimeoutError() from exc
    except httpx2.RequestError as exc:
        raise LLMServiceError(f"LLM 网络请求失败：{exc}") from exc

    if response.status_code == 401:
        raise BusinessException(code=50003, message="LLM 凭证无效", status_code=502)
    if response.status_code == 429:
        raise BusinessException(code=42901, message="LLM 限流，请稍后重试", status_code=429)
    if response.status_code >= 400:
        raise LLMServiceError(f"LLM 返回 {response.status_code}: {response.text[:200]}")

    try:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError("LLM 响应结构不符合预期") from exc

    return {
        "content": content,
        "usage": _usage_from(body),
        "model": body.get("model", settings.llm_model),
    }


def get_llm_http(request: Request) -> httpx2.AsyncClient:
    """从 app.state 取出 lifespan 创建的共享客户端。"""
    return request.app.state.llm_http


async def chat_stream(
    http: httpx2.AsyncClient,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
    """流式对话：边收边吐内容增量（async generator）。

    OpenAI-compatible 的流式响应是若干行：
        data: {"choices":[{"delta":{"content":"你"}}]}
        data: [DONE]
    """
    settings = get_settings()
    if not settings.llm_api_key:
        raise BusinessException(
            code=50002, message="未配置 LLM_API_KEY，请在 .env 里填写", status_code=500
        )

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    try:
        async with http.stream(
            "POST",
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        ) as response:
            if response.status_code == 401:
                raise BusinessException(code=50003, message="LLM 凭证无效", status_code=502)
            if response.status_code == 429:
                raise BusinessException(
                    code=42901, message="LLM 限流，请稍后重试", status_code=429
                )
            if response.status_code >= 400:
                body = await response.aread()
                raise LLMServiceError(f"LLM 返回 {response.status_code}: {body[:200]!r}")

            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    # 半截 JSON 跳过，流不能因为一行坏掉就整体中断
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = (choices[0].get("delta") or {}).get("content")
                if delta:
                    yield delta
    except httpx2.TimeoutException as exc:
        raise LLMTimeoutError() from exc
    except httpx2.RequestError as exc:
        raise LLMServiceError(f"LLM 网络请求失败：{exc}") from exc