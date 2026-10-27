"""LLM 客户端单元测试：用 MockTransport，不联网、不花钱。"""

import asyncio
import json

import httpx2
import pytest

from app.core.config import get_settings
from app.services.llm_client import LLMServiceError, LLMTimeoutError, chat_once
from app.utils.errors import BusinessException
from asyncio import run

@pytest.fixture(autouse=True)
def fake_settings(monkeypatch):
    """把配置换成测试值，并清掉 lru_cache，否则读到的是旧配置。"""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://fake.local")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def run_with(handler):
    """用一个假的 HTTP 处理器跑一次 chat_once。"""

    async def run():
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler),
            base_url="https://fake.local",
        ) as http:
            return await chat_once(http, [{"role": "user", "content": "你好"}])

    return asyncio.run(run())


def test_success_parses_content_and_usage():
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "test-model"

        return httpx2.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"message": {"content": "你好，我是模型"}}],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 5,
                    "total_tokens": 8,
                },
            },
        )

    result = run_with(handler)

    assert result["content"] == "你好，我是模型"
    assert result["usage"]["total_tokens"] == 8
    assert result["model"] == "test-model"


def test_401_raises_business_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(401, json={"error": "invalid key"})

    with pytest.raises(BusinessException) as exc_info:
        run_with(handler)

    assert exc_info.value.code == 50003


def test_429_raises_rate_limit_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(429, json={"error": "rate limited"})

    with pytest.raises(BusinessException) as exc_info:
        run_with(handler)

    assert exc_info.value.code == 42901


def test_truncated_json_raises_service_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text='{"choices": [{"message": {"content": "半')

    with pytest.raises(LLMServiceError):
        run_with(handler)


def test_missing_choices_raises_service_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"model": "test-model"})

    with pytest.raises(LLMServiceError):
        run_with(handler)


def test_timeout_raises_timeout_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("模拟超时", request=request)

    with pytest.raises(LLMTimeoutError):
        run_with(handler)
