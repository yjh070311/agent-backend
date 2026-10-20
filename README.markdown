# agent-backend

AI Agent 应用的后端服务骨架：FastAPI+SQLAlchemy+JWT,作为'AI-interview'模拟面试系统的额服务层地基

## 功能

- JWT登录认证（PBKDF2 密码哈希、Bearer Token）
- 用户/会话/消息三层数据模型，级联删除
- 会话 CRUD + 消息分页查询，按用户隔离
- 统一响应外壳 '{code,message,data}' 与统一的错误码体系
- 全局异常处理 （业务/校验/HTTP/未捕获）
- 请求追踪：每个响应带 'X-Request-ID' ，日志按请求串联
- pytest 自动化测试（临时数据库，不依赖真实数据）

## 技术栈

| 技术 | 用途 |
| --- | --- |
| FastAPI 0.141 | Web 框架 |
| SQLAlchemy 2.1 | ORM |
| SQLite | 开发数据库（后续PostgreSQL）|
| PyJWT | 令牌签发与校验 |
| Pydantic 2 | 请求校验与响应模型 |
| Pytest | 自动化测试 |

## 架构

```text
HTTP → routers（接参数、调逻辑）
        ↓
      schemas（校验输入 / 定义输出）
        ↓
      models（描述数据）
        ↓
      database（会话管理）

横切：core.middleware（request_id + 耗时）
      utils.errors（统一异常与错误码）
      utils.deps（当前登录用户）
```

依赖方向从上往下

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env      # 然后填入你自己的 JWT_SECRET
python init_db.py                # 建表
python -m uvicorn app.main:app --reload
```
打开 http://127.0.0.1:8000/docs 。

## 接口

| 方法 | 路径 | 说明 | 认证 |
| --- | --- | --- | --- |
| POST | `/auth/register` | 注册 | 否 |
| POST | `/auth/login` | 登录换取 token | 否 |
| GET | `/conversation` | 会话列表（分页） | 是 |
| POST | `/conversation` | 创建会话 | 是 |
| GET | `/conversation/{id}` | 会话详情 | 是 |
| PATCH | `/conversation/{id}` | 修改标题 | 是 |
| DELETE | `/conversation/{id}` | 删除会话 | 是 |
| GET | `/conversation/{id}/messages` | 消息分页 | 是 |
| GET | `/health` | 健康检查 | 否 |

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

测试使用 `dependency_overrides` 把数据库换成 `tmp_path` 下的临时 SQLite，
不会读写 `data/agent_backend.db`。

## 已知限制

- 数据库为 SQLite，未做并发写优化；后续迁移 PostgreSQL。
- access token 有效期 2 小时，暂无 refresh token。
- 消息只有查询接口，创建接口待补。
- 日志输出到标准输出，未做文件轮转。

## 后续计划

- Week 3：接入 LLM，实现简历解析与岗位匹配 API
- 后续：面试题库 RAG、Agent 流程编排、Docker Compose 部署