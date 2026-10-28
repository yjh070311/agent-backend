import asyncio
import httpx2
import pytest

from app.core.config import get_settings
from app.services.llm_client import chat_stream
from app.utils.errors import BusinessException


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://fake.local")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_body(*chunks: str) -> bytes:
    lines = [
        "data: " + '{"choices":[{"delta":{"content":"%s"}}]}' % chunk for chunk in chunks
    ]
    lines.append("data: [DONE]")
    return ("\n\n".join(lines) + "\n\n").encode("utf-8")


def run_stream(body: bytes, status: int = 200) -> list[str]:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status, content=body, headers={"content-type": "text/event-stream"}
        )

    async def run():
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler), base_url="https://fake.local"
        ) as http:
            return [
                delta
                async for delta in chat_stream(
                    http, [{"role": "user", "content": "你好"}]
                )
            ]

    return asyncio.run(run())


def test_yields_deltas_in_order():
    assert run_stream(make_body("你", "好")) == ["你", "好"]


def test_ignores_non_data_lines_and_broken_json():
    body = (
        b"event: ping\n\n"
        b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
        b"data: {broken json\n\n"
        b"data: [DONE]\n\n"
    )
    assert run_stream(body) == ["hello"]


def test_stops_at_done_marker():
    ignored = 'data: {"choices":[{"delta":{"content":"不该出现"}}]}\n\n'
    assert run_stream(make_body("A") + ignored.encode("utf-8")) == ["A"]


def test_401_raises_before_yielding():
    with pytest.raises(BusinessException) as exc_info:
        run_stream(b"", status=401)
    assert exc_info.value.code == 50003
