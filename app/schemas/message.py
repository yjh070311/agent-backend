"""消息接口的pydantic模型"""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageOut(BaseModel):
    """消息的响应体。"""

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListQuery:
    