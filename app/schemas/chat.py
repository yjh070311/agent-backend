"""
对话接口的请求/响应模型
1.增加field校验
2.增加嵌套模型message
3.响应增加usage和created_at字段

Pydantic的价值在此体现：
    业务逻辑拿到的永远是干净的对象
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Message(BaseModel):
    """单条对话消息，对应 OpenAI-compatible API 的 messages 元素。"""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"] = Field(
        description="消息角色：system/user/assistant",
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
        description="消息内容",
    )

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("消息内容不能只包含空白字符")
        return value


class ChatRequest(BaseModel):
    """对话请求体，包含多轮消息和生成参数。"""

    model_config = ConfigDict(extra="forbid")

    messages: list[Message] = Field(
        min_length=1,
        max_length=50,
        description="完整对话消息列表",
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度，0=确定性强，2=创造性强",
    )

    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="最大输出 token 数",
    )

    @model_validator(mode="after")
    def must_include_user_message(self) -> "ChatRequest":
        if not any(message.role == "user" for message in self.messages):
            raise ValueError("messages 至少包含一条 user 消息")
        return self

    @property
    def last_user_message(self) -> str:
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content

        raise ValueError("messages 至少包含一条 user 消息")


class TokenUsage(BaseModel):
    """Token 用量统计，嵌套在响应中。"""

    prompt_tokens: int = Field(ge=0, description="输入 token 数")
    completion_tokens: int = Field(ge=0, description="输出 token 数")
    total_tokens: int = Field(ge=0, description="总 token 数")


class ChatResponse(BaseModel):
    """对话响应体。"""

    reply: str = Field(description="助手回复内容")

    model: str = Field(description="使用的模型名")
    usage: TokenUsage | None = Field(
        default=None,
        description="Token 用量统计",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="响应生成时间（UTC）",
    )