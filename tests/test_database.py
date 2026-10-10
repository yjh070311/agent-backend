import unittest
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, delete, event, func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Conversation, Message, User
from test_orm import query_messages_by_role


class DatabaseModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(
            dbapi_connection: SQLiteConnection,
            connection_record: object,
        ) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_insert_and_load_related_conversations_and_messages(self) -> None:
        user = User(username="test-user", password_hash="test-hash")
        conversation = Conversation(title="Test conversation")
        conversation.messages.extend(
            [
                Message(role="user", content="Question"),
                Message(role="assistant", content="Answer"),
            ]
        )
        user.conversations.append(conversation)
        self.session.add(user)
        self.session.commit()

        loaded_user = self.session.scalars(
            select(User)
            .options(selectinload(User.conversations).selectinload(Conversation.messages))
            .where(User.username == "test-user")
        ).one()

        self.assertEqual(len(loaded_user.conversations), 1)
        self.assertEqual(len(loaded_user.conversations[0].messages), 2)
        self.assertEqual(
            [message.role for message in loaded_user.conversations[0].messages],
            ["user", "assistant"],
        )

    def test_query_messages_by_role_returns_newest_first_and_empty_list(self) -> None:
        conversation = Conversation(
            user=User(username="query-user", password_hash="test-hash"),
            messages=[
                Message(role="user", content="First"),
                Message(role="assistant", content="Reply"),
                Message(role="user", content="Second"),
            ],
        )
        self.session.add(conversation)
        self.session.commit()

        messages = query_messages_by_role(self.session, conversation.id, "user")
        self.assertEqual([message.content for message in messages], ["Second", "First"])
        self.assertEqual(
            query_messages_by_role(self.session, conversation.id, "system"),
            [],
        )

    def test_deleting_user_cascades_to_conversations_and_messages(self) -> None:
        user = User(
            username="cascade-user",
            password_hash="test-hash",
            conversations=[
                Conversation(messages=[Message(role="user", content="Question")])
            ],
        )
        self.session.add(user)
        self.session.commit()
        conversation_id = user.conversations[0].id

        self.session.delete(user)
        self.session.commit()

        remaining_conversations = self.session.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.id == conversation_id)
        )
        remaining_messages = self.session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        self.assertEqual(remaining_conversations, 0)
        self.assertEqual(remaining_messages, 0)

    def test_sqlite_foreign_key_cascade_works_for_direct_delete(self) -> None:
        user = User(
            username="database-cascade-user",
            password_hash="test-hash",
            conversations=[
                Conversation(messages=[Message(role="user", content="Question")])
            ],
        )
        self.session.add(user)
        self.session.commit()
        conversation_id = user.conversations[0].id
        foreign_keys_enabled = self.session.connection().exec_driver_sql(
            "PRAGMA foreign_keys"
        ).scalar_one()
        self.assertEqual(foreign_keys_enabled, 1)

        self.session.execute(delete(User).where(User.id == user.id))
        self.session.commit()

        remaining_conversations = self.session.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.id == conversation_id)
        )
        remaining_messages = self.session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        self.assertEqual(remaining_conversations, 0)
        self.assertEqual(remaining_messages, 0)


if __name__ == "__main__":
    unittest.main()
