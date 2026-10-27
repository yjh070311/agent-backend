"""pytest 共享 fixture：每个用例一个临时数据库 + 一个登录好的客户端。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
import app.models  # noqa: F401
from app.main import app


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},   # 布尔值！
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # 用 with 进入 context，lifespan 才会执行
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client) -> dict[str, str]:
    payload = {"username": "alice", "password": "passw0rd123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_user_headers(client) -> dict[str, str]:
    payload = {"username": "bob", "password": "passw0rd456"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}