"""会话接口测试：CRUD、分页、越权隔离。"""


def test_create_conversation_returns_201_and_owner(client, auth_headers):
    response = client.post(
        "/conversation",
        json={"title": "我的面试"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "我的面试"
    assert data["user_id"] == 1


def test_list_returns_total_not_page_size(client, auth_headers):
    for index in range(3):
        client.post(
            "/conversation",
            json={"title": f"会话{index}"},
            headers=auth_headers,
        )

    response = client.get("/conversation?limit=2&offset=0", headers=auth_headers)

    assert response.status_code == 200
    page = response.json()["data"]
    assert len(page["items"]) == 2
    assert page["total"] == 3  # total 是总数，不是本页条数


def test_get_conversation_detail(client, auth_headers):
    created = client.post(
        "/conversation",
        json={"title": "详情"},
        headers=auth_headers,
    ).json()["data"]

    response = client.get(f"/conversation/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_patch_updates_only_provided_fields(client, auth_headers):
    created = client.post(
        "/conversation",
        json={"title": "旧标题"},
        headers=auth_headers,
    ).json()["data"]

    response = client.patch(
        f"/conversation/{created['id']}",
        json={"title": "新标题"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "新标题"


def test_other_user_cannot_read_conversation(client, auth_headers, second_user_headers):
    created = client.post(
        "/conversation",
        json={"title": "alice 的会话"},
        headers=auth_headers,
    ).json()["data"]

    response = client.get(
        f"/conversation/{created['id']}",
        headers=second_user_headers,
    )

    # 越权必须是 404，不能是 403：403 会暴露「这个资源确实存在」
    assert response.status_code == 404
    assert response.json()["code"] == 40402


def test_delete_then_read_returns_404(client, auth_headers):
    created = client.post(
        "/conversation",
        json={"title": "待删除"},
        headers=auth_headers,
    ).json()["data"]

    assert client.delete(
        f"/conversation/{created['id']}",
        headers=auth_headers,
    ).status_code == 204
    assert client.get(
        f"/conversation/{created['id']}",
        headers=auth_headers,
    ).status_code == 404

