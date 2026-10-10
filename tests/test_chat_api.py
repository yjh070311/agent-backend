import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


class ChatApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_valid_request_returns_typed_response_and_defaults(self) -> None:
        response = self.client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "你好"}]},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model"], "echo-model")
        self.assertEqual(body["usage"]["prompt_tokens"], 2)
        self.assertEqual(
            body["usage"]["total_tokens"],
            body["usage"]["prompt_tokens"] + body["usage"]["completion_tokens"],
        )
        created_at = datetime.fromisoformat(body["created_at"])
        self.assertIsNotNone(created_at.tzinfo)

    def test_multi_turn_request_uses_last_user_message(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "system", "content": "你是 AI 助手"},
                    {"role": "user", "content": "第一问"},
                    {"role": "assistant", "content": "回答"},
                    {"role": "user", "content": "最后一问"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("最后一问", response.json()["reply"])

    def test_pydantic_coerces_numeric_strings(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "messages": [{"role": "user", "content": "你好"}],
                "temperature": "0.7",
                "max_tokens": "128",
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_invalid_requests_return_422(self) -> None:
        invalid_payloads = [
            {},
            {"messages": []},
            {"messages": [{"role": "admin", "content": "你好"}]},
            {"messages": [{"role": "user", "content": ""}]},
            {"messages": [{"role": "user", "content": "   "}]},
            {"messages": [{"role": "assistant", "content": "不能代替用户提问"}]},
            {"messages": [{"role": "user", "content": "你好", "unexpected": True}]},
            {
                "messages": [{"role": "user", "content": "你好"}],
                "temperature": 5,
            },
            {"messages": [{"role": "user", "content": "你好"}], "unknown": True},
            {"messages": [{"role": "user", "content": "x" * 10001}]},
            {
                "messages": [
                    {"role": "user", "content": f"消息{i}"} for i in range(51)
                ],
            },
            {
                "messages": [{"role": "user", "content": "你好"}],
                "temperature": "not-a-number",
            },
            {
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 0,
            },
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/chat", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertIn("detail", response.json())


if __name__ == "__main__":
    unittest.main()
