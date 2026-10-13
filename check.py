"""Day 12 验收脚本：不启动服务器，直接对 app.main 做四类故障 + 一个正常请求的检查。

用法（在 agent-backend 根目录执行）：
    .venv/Scripts/python.exe selfcheck_day12.py
如果终端中文乱码，先执行：$env:PYTHONIOENCODING="utf-8"

它把数据库依赖替换成临时库，不会碰你的 data/agent_backend.db。
"""

import pathlib
import sys
import tempfile

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if (PROJECT_ROOT / "app").is_dir():
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
import app.models  # noqa: E402,F401
from app.main import app  # noqa: E402

tmp_db = pathlib.Path(tempfile.mkdtemp(prefix="day12_")) / "check.db"
engine = create_engine(
    f"sqlite:///{tmp_db}",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)

failures: list[str] = []

print("=" * 78)
print("1) 四类故障：状态码 + 响应外壳 + X-Request-ID")
print("=" * 78)

cases = [
    ("业务异常：不存在的会话", "GET", "/conversation/99999", None, 404),
    ("校验异常：空标题", "POST", "/conversation", {"title": ""}, 422),
    ("框架异常：路径不存在", "GET", "/not-exist-path", None, 404),
    ("未处理异常：/boom", "GET", "/boom", None, 500),
]

for label, method, url, body, expected in cases:
    if method == "GET":
        response = client.get(url)
    else:
        response = client.post(url, json=body)

    headers = response.headers
    request_id = headers.get("X-Request-ID") or headers.get("X-Request_ID")
    try:
        payload = response.json()
        shaped = set(payload) == {"code", "message", "data"}
    except Exception:
        payload, shaped = {}, False

    problems = []
    if response.status_code != expected:
        problems.append(f"状态码应为 {expected}")
    if not shaped:
        problems.append("响应外壳不是 {code, message, data}")
    if not request_id:
        problems.append("缺少 X-Request-ID 响应头")
    if problems:
        failures.append(f"{label}: {'；'.join(problems)}")

    flag = "OK  " if not problems else "FAIL"
    print(f"[{flag}] {label:<22} {response.status_code} (期望 {expected})  req_id={request_id}")
    print(f"        body: {str(payload)[:110]}")

print()
print("=" * 78)
print("2) 正常路径：创建会话")
print("=" * 78)

created = client.post("/conversation", json={"title": "验收用例"})
if created.status_code != 201:
    failures.append(f"创建会话应为 201，实际 {created.status_code}")
print(f"[{'OK  ' if created.status_code == 201 else 'FAIL'}] POST /conversation -> {created.status_code}")
print(f"        body: {created.text[:160]}")

listed = client.get("/conversation")
if listed.status_code != 200:
    failures.append(f"会话列表应为 200，实际 {listed.status_code}")
print(f"[{'OK  ' if listed.status_code == 200 else 'FAIL'}] GET  /conversation -> {listed.status_code}")

print()
print("=" * 78)
if failures:
    print(f"结论：{len(failures)} 项不通过")
    for item in failures:
        print(f"  - {item}")
else:
    print("结论：Day 12 全部通过。")
