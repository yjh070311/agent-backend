"""每个用例都有临时数据库+客户端"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base,get_db
import app.models
from app.main import app

@pytest.fixture()
def client(tmp_path):
    """每个用例独立数据库，不互相污染"""
    engine=create_engine(
        f"sqlite:///{tmp_path/'test.db'}",
        connect_args={"check_same_thread":False},
    )
    TestingSession=sessionmaker(bind=engine,autoflush=False)
    Base.metadata.create_all(bind=engine)   #metadata收集所有用例中定义的模型，create_all创建所有表


    def override_get_db():
        db=TestingSession()
        try:
            yield db
        finally:
            db.close()


    app.dependency_overrides[get_db]=override_get_db

    yield  TestClient(app,raise_server_exceptions=False)

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client)->dict[str,str]:
    """注册并登录一个用户,返回可用表头"""
    payload={"username":"alice","password":"password123"}
    client.post("/auth/register",json=payload)
    response=client.post("/auth/login",json=payload)
    token=response.json()["data"]["access_token"]
    return {"Authorization":f"Bearer {token}"}

@pytest.fixture()
def second_user_headers(client)->dict[str,str]:
    """验证隔离数据"""
    payload = {"username": "bob", "password": "passw0rd456"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}