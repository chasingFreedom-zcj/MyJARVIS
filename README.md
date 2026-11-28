# MyJARVIS

MyJARVIS 是一个面向 AI 应用开发岗位的作品项目，目标是把用户输入的模糊目标转化为可执行计划，并在执行过程中持续跟进、调整和复盘。

当前处于工程基线阶段，已经完成 FastAPI 后端、统一配置、结构化日志、统一异常响应、健康检查、本地 Docker 服务、自动化测试和 GitHub Actions 后端 CI。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic v2 / pydantic-settings
- SQLAlchemy 2.0 async
- PostgreSQL 16
- Redis
- Mailpit
- uv
- Ruff
- mypy
- pytest
- Docker Compose
- GitHub Actions

## 环境要求

- Windows、macOS 或 Linux
- Python 3.12
- uv
- Docker Desktop 或其他 Docker Engine
- Git

检查基础环境：

```powershell
python --version
uv --version
docker --version
docker compose version
```

启动 Docker Desktop，并确认：

```powershell
docker info --format "{{.ServerVersion}}"
```

能够输出版本号说明 Docker Engine 正常运行。

## 项目结构

```text
MyJARVIS/
├── .github/
│   └── workflows/
│       └── backend-ci.yml
├── backend/
│   ├── app/
│   │   ├── core/          # 配置、日志和异常处理
│   │   ├── crud/          # 数据访问层
│   │   ├── db/            # 数据库连接
│   │   ├── middleware/    # 请求上下文
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── routers/       # API 路由
│   │   ├── schemas/       # Pydantic Schema
│   │   └── main.py        # FastAPI 入口
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
├── compose.yaml
├── .env.example
└── README.md
```

## 1. 配置环境变量

进入项目根目录：

```powershell
cd C:\Projects\MyJARVIS
```

仅当本地还没有 `.env` 时，从模板创建：

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

不要覆盖已有的 `.env`。

检查以下关键配置：

```dotenv
DATABASE_URL=postgresql+asyncpg://myjarvis:myjarvis_dev@127.0.0.1:5432/myjarvis
REDIS_URL=redis://127.0.0.1:6379/0

DEEPSEEK_API_KEY=
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_ID=deepseek-flash
```

如果暂时不测试大模型接口，`DEEPSEEK_API_KEY` 可以保持为空。

`.env` 包含本机密钥，已经被 `.gitignore` 排除，禁止提交到 Git。

## 2. 启动本地基础设施

```powershell
docker compose up -d --wait
docker compose ps
```

预期服务：

| 服务 | 地址 | 用途 |
|---|---|---|
| PostgreSQL | `127.0.0.1:5432` | 主业务数据库 |
| Redis | `127.0.0.1:6379` | 缓存、队列和短期状态 |
| Mailpit SMTP | `127.0.0.1:1025` | 开发邮件接收 |
| Mailpit Web | http://127.0.0.1:8025 | 查看开发邮件 |

PostgreSQL 和 Redis 应显示为 `healthy`。

查看日志：

```powershell
docker compose logs --tail=100
```

停止服务但保留数据：

```powershell
docker compose down
```

不要随意执行：

```powershell
docker compose down -v
```

该命令会删除 PostgreSQL 和 Redis 的数据卷。

## 3. 安装后端依赖

```powershell
cd C:\Projects\MyJARVIS\backend
uv sync --locked --group dev
```

`uv run` 会自动使用项目虚拟环境，通常不需要手动激活 `.venv`。

## 4. 启动后端

```powershell
cd C:\Projects\MyJARVIS\backend
uv run uvicorn app.main:app --reload
```

启动地址：

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs
- OpenAPI JSON：http://127.0.0.1:8000/openapi.json

## 5. 健康检查

存活检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
```

依赖就绪检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

预期：

```text
status checks
------ ------
ok     @{database=; redis=}
```

数据库和 Redis 正常时返回 HTTP 200；任一依赖不可用时返回 HTTP 503。

说明：当前迁移阶段之前，如果你的真实 `.env` 仍指向 MySQL，`/health/ready` 的数据库检查会失败。后续数据库迁移阶段会统一切换到 PostgreSQL。

## 6. 质量检查

进入后端目录：

```powershell
cd C:\Projects\MyJARVIS\backend
```

自动格式化并修复：

```powershell
uv run ruff format app tests
uv run ruff check --fix app tests
```

最终验收：

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
uv run mypy app
uv run pytest -q
```

只有全部通过后再提交代码。

## 7. 持续集成

`.github/workflows/backend-ci.yml` 会在每次推送相关代码时运行：

- Ruff 静态检查
- Ruff 格式检查
- mypy 类型检查
- pytest 自动化测试

CI 使用的是临时 Ubuntu Runner。它只检查已经提交并推送的代码，不会修改本地文件，也不会自动修复仓库中的代码。

## 配置原则

- 真实环境和密钥写入 `.env`，不提交。
- 可提交的变量模板写入 `.env.example`。
- 应用读取配置时统一通过 `app.core.config.Settings`。
- 容器端口配置写入 `compose.yaml`。
- 日志不得记录密码、完整 Token、API Key 或用户隐私正文。
- 开发数据库密码只用于本地，不能用于生产环境。

## 常见问题

### 出现 `No module named 'app'`

确认从 `backend` 目录运行：

```powershell
cd C:\Projects\MyJARVIS\backend
uv run pytest -q
```

同时确认 `pyproject.toml` 包含：

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

### Docker 报错 `permission denied`

确认 Docker Desktop 已启动，并显示 `Engine running`。必要时重启 Docker Desktop。

### 端口已被占用

检查端口占用：

```powershell
Get-NetTCPConnection -LocalPort 5432,6379,1025,8025
```

关闭冲突程序，或在 `.env` 中修改对应的 `_PORT` 变量。

### 健康检查数据库不可用

检查容器：

```powershell
docker compose ps
docker compose logs postgres
```

并确认 `.env` 中的 `DATABASE_URL` 与 Compose 的数据库名、用户、密码和端口一致。