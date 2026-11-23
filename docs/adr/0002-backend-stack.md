# ADR-002：后端采用 Python 3.12 + FastAPI + SQLAlchemy

- 状态：Accepted
- 日期：2026-11-22
- 决策者：项目所有者

## 背景

当前项目已经包含 FastAPI、异步 SQLAlchemy、Alembic 和 DeepSeek 兼容调用。目标是为 PWA 提供类型明确的 API，并让 Agent 调用、后台任务和数据库访问共享同一套业务规则。

## 决策

后端采用以下技术栈：

- Python 3.12。
- `uv` 管理依赖和锁定版本。
- FastAPI。
- Pydantic v2 和 `pydantic-settings`。
- SQLAlchemy 2.x async。
- Alembic 管理数据库迁移。
- Ruff 进行格式和静态检查。
- mypy 进行类型检查。
- pytest 和 httpx 进行测试。
- OpenAPI 生成前端 TypeScript 类型。

## 选择理由

- FastAPI 的依赖注入和 OpenAPI 支持适合定义用户 API 与 Agent 工具边界。
- Pydantic 可以统一校验 REST 请求、模型输出和工具参数。
- SQLAlchemy async 与 FastAPI 的异步请求模型一致。
- Alembic 能保留明确、可回退的数据库结构历史。
- Python 3.12 对当前依赖兼容性较好，容器镜像和工具链成熟。
- `uv` 能提供可复现安装，并在 CI 和 Docker 中保持一致。

## 备选方案

### Python 3.13 或 3.14

新版本性能和语言能力更好，但在 P1 需要通过完整依赖和 Docker 兼容性验证后才能替代 3.12。若升级，应新增 ADR。

### Django REST Framework

适合传统 CRUD、后台和认证，但当前项目已经采用 FastAPI，且 Agent SSE、自定义工具和异步服务更直接。

### Flask

更轻量，但需要自行补充大量类型、文档和异步生态。

## 关键约束

1. API schema、工具 schema 和领域对象要有明确转换边界。
2. 事务由 application service 控制，不在 router 或 repository 中随意提交。
3. 模型输出必须经过 Pydantic 校验。
4. 数据库迁移只能通过 Alembic 执行，不使用 `create_all` 作为正式建表方式。
5. 生产依赖必须从锁文件安装。

## 后果和代价

- 需要维护 Pydantic schema 与 SQLAlchemy model 的转换。
- 类型检查会增加前期工作量，但能减少运行时错误。
- Python 3.12 需要与当前开发机中的 Python 3.14 明确区分，P1 必须验证 `.venv` 和 Docker 使用同一版本。

## 验证方式

- 新环境可以从锁文件安装全部依赖。
- CI 中 Ruff、mypy、pytest 可以通过。
- FastAPI OpenAPI 能生成前端 TypeScript 类型。
- 本地和 Docker 使用相同主版本 Python。

## 后续待办

- 在 P1 创建 `pyproject.toml` 和锁文件。
- 清理当前不完整依赖和无关导入。
- 建立统一配置、日志和异常响应。
