"""Message ORM model mapped to the messages table."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    """消息表——单条对话消息。

    一条消息属于一个会话（多对一）。
    role 和 content 对应 LLM messages 的结构（复用 Week 1 的概念）。
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # role 用 String 而非 Enum——保留灵活性，校验放在 Pydantic 层
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Text 用于长内容，String 有长度限制，Text 更适合 LLM 消息
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 反向关系
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<Message id={self.id} role={self.role} content={preview!r}>"
