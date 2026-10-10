"""Demonstrate inserting, querying, and deleting a User → Conversation → Message graph.

Run after init_db.py:
    .venv\\Scripts\\python.exe test_orm.py
"""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal
from app.models import Conversation, Message, User


def query_messages_by_role(
    db: Session,
    conversation_id: int,
    role: str,
) -> list[Message]:
    """Return messages of a role in one conversation, newest first."""
    statement = (
        select(Message)
        .filter(
            Message.conversation_id == conversation_id,
            Message.role == role,
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
    )
    return db.scalars(statement).all()


def demo_crud() -> None:
    """Create linked rows, read them through relationships, then verify cascade delete."""
    username = f"day10_{uuid4().hex}"

    with SessionLocal() as db:
        try:
            user = User(username=username, password_hash="demo-hash-not-a-real-password")
            conversation = Conversation(title="Day 10 ORM 演示")
            conversation.messages.extend(
                [
                    Message(role="user", content="什么是 ORM？"),
                    Message(role="assistant", content="ORM 将 Python 对象映射到数据库表。"),
                ]
            )
            user.conversations.append(conversation)

            print(f"Before add: user.id={user.id}")
            db.add(user)
            db.flush()
            print(f"After flush (not committed): user.id={user.id}")
            db.commit()

            fetched_user = db.scalars(
                select(User)
                .options(
                    selectinload(User.conversations).selectinload(Conversation.messages)
                )
                .where(User.id == user.id)
            ).one()

            print(f"User: {fetched_user.username}")
            for fetched_conversation in fetched_user.conversations:
                print(
                    f"  Conversation: {fetched_conversation.title} "
                    f"({len(fetched_conversation.messages)} messages)"
                )
                for message in fetched_conversation.messages:
                    print(f"    [{message.role}] {message.content}")

            user_messages = query_messages_by_role(
                db,
                conversation.id,
                "user",
            )
            print(f"User-role message query returned {len(user_messages)} row(s).")

            fetched_user_id = fetched_user.id
            db.delete(fetched_user)
            db.commit()
            remaining_user = db.get(User, fetched_user_id)
            print(f"After deleting user, user lookup is {remaining_user}.")
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    demo_crud()
