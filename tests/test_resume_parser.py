"""简历解析测试：全部用 MockTransport，不联网、不花钱。"""

import asyncio
import json

import httpx2
import pytest

from app.core.config import get_settings
from app.schemas.resume import ResumeProfile
from app.services.resume_parser import ResumeParseError, parse_resume_text, strip_code_fences


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://fake.local")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


VALID_PROFILE = {
    "name": "张三",
    "years_experience": 1,
    "skills": ["Python", "FastAPI", "RAG"],
    "education": [
        {"school": "杭州电子科技大学", "major": "智能科学与技术",
         "degree": "本科", "start": "2025", "end": "2029"}
    ],
    "projects": [
        {"name": "AI-Interview", "role": "后端",
         "tech": ["FastAPI", "RAG"], "highlights": ["完成闭环"]}
    ],
    "target_roles": ["AI Agent 开发实习"],
    "summary": "有 LLM 应用开发经验的学生",
}


def run_with(handler, text: str = "张三，杭州电子科技大学，熟悉 Python 和 FastAPI。"):
    async def run():
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler),
            base_url="https://fake.local",
        ) as http:
            return await parse_resume_text(http, text)

    return asyncio.run(run())


def test_strip_code_fences():
    assert strip_code_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert strip_code_fences('{"a": 1}') == '{"a": 1}'


def test_parses_valid_json():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={
            "model": "test-model",
            "choices": [{"message": {"content": json.dumps(VALID_PROFILE, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        })

    profile = run_with(handler)

    assert isinstance(profile, ResumeProfile)
    assert profile.name == "张三"
    assert "FastAPI" in profile.skills
    assert profile.projects[0].name == "AI-Interview"


def test_parses_json_wrapped_in_code_fence():
    def handler(request: httpx2.Request) -> httpx2.Response:
        content = "```json\n" + json.dumps(VALID_PROFILE, ensure_ascii=False) + "\n```"
        return httpx2.Response(200, json={
            "model": "test-model",
            "choices": [{"message": {"content": content}}],
            "usage": {},
        })

    profile = run_with(handler)

    assert profile.name == "张三"
    assert len(profile.education) == 1


def test_retries_once_when_first_output_is_broken():
    calls = {"n": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            content = "抱歉，我无法解析这份简历。"
        else:
            content = json.dumps(VALID_PROFILE, ensure_ascii=False)
        return httpx2.Response(200, json={
            "model": "test-model",
            "choices": [{"message": {"content": content}}],
            "usage": {},
        })

    profile = run_with(handler)

    assert calls["n"] == 2
    assert profile.name == "张三"


def test_raises_after_two_failures():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={
            "model": "test-model",
            "choices": [{"message": {"content": "不是 JSON"}}],
            "usage": {},
        })

    with pytest.raises(ResumeParseError) as exc_info:
        run_with(handler)

    assert exc_info.value.code == 42210
    assert exc_info.value.status_code == 422


def test_missing_optional_fields_get_defaults():
    def handler(request: httpx2.Request) -> httpx2.Response:
        minimal = {"name": "李四", "skills": ["Python"]}
        return httpx2.Response(200, json={
            "model": "test-model",
            "choices": [{"message": {"content": json.dumps(minimal, ensure_ascii=False)}}],
            "usage": {},
        })

    profile = run_with(handler)

    assert profile.name == "李四"
    assert profile.projects == []
    assert profile.years_experience == 0


def test_empty_text_raises_without_calling_model():
    calls = {"n": 0}

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls["n"] += 1
        return httpx2.Response(200, json={})

    with pytest.raises(ResumeParseError):
        run_with(handler, text="   ")

    assert calls["n"] == 0