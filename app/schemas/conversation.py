"""
会话接口的pydantic模型
"""

from datetime import datetime

from pydantic import BaseModel,Field

class ConversationCreate(BaseModel):
    """创建会话请求体"""
    title:str=Field(
        default="新对话",
        min_length=1,
        max_length=100,
        description="会话标题",
    )

class ConversationUpdate(BaseModel):
    """更新会话的请求体（字段都可选，只更新传入的字段）。"""
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="新的会话标题",
    )


class ConversationOut(BaseModel):
    """会话的响应体（从 ORM 模型转出的安全输出）。

    注意：不包含 user_id 之外不该暴露的字段。
    """

    id: int
    title: str
    user_id: int
    created_at: datetime

    # 让 Pydantic 能从 ORM 对象直接转换
    # 这是 SQLAlchemy 和 Pydantic 协作的关键配置
    model_config = {"from_attributes": True}    