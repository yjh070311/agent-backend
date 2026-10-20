"""认证接口测试：注册 / 登录 / 认证失败。"""


def test_register_returns_201_and_hides_password_hash(client):
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "passw0rd123"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["username"] == "alice"
    assert set(data) == {"id", "username", "created_at"}  # 不能有 password_hash


def test_register_duplicate_username_returns_409(client):
    payload = {"username": "alice", "password": "passw0rd123"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["code"] == 40901


def test_register_short_password_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "123"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == 42200


def test_login_returns_token(client):
    payload = {"username": "alice", "password": "passw0rd123"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 7200


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"username": "alice", "password": "passw0rd123"},
    )

    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40101


def test_login_unknown_user_returns_same_message_as_wrong_password(client):
    """防用户名枚举：两种情况返回同一句话。"""
    client.post(
        "/auth/register",
        json={"username": "alice", "password": "passw0rd123"},
    )

    wrong_password = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )
    unknown_user = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "passw0rd123"},
    )

    assert wrong_password.json()["message"] == unknown_user.json()["message"]


def test_request_without_token_returns_401(client):
    response = client.get("/conversation")

    assert response.status_code == 401
    assert response.json()["code"] == 40101


def test_request_with_invalid_token_returns_401(client):
    response = client.get(
        "/conversation",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401