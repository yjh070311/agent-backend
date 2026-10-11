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


class MessageListQuery(BaseModel):
    """消息列表查询"""
    limit:int=Field(default=20,ge=1,le=100,description="每页条数")
    offset:int=Field(default=0,ge=0,description="偏移量")