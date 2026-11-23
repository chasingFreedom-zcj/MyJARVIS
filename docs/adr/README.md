# MyJARVIS 架构决策记录

本目录记录 MyJARVIS 的长期架构决策。实施过程中不能随意绕过已接受的 ADR；如果选择发生变化，应新增 ADR，并将旧决策标记为 `Superseded`。

## 决策索引

| ADR | 决策 | 状态 |
|---|---|---|
| [ADR-001](0001-modular-monolith.md) | 采用模块化单体与 API-first 架构 | Accepted |
| [ADR-002](0002-backend-stack.md) | 后端采用 Python 3.12 + FastAPI + SQLAlchemy | Accepted |
| [ADR-003](0003-postgresql.md) | 使用 PostgreSQL 作为主数据库 | Accepted |
| [ADR-004](0004-authentication.md) | 使用邮箱密码、JWT 与安全 Cookie 认证 | Accepted |
| [ADR-005](0005-agent-orchestration.md) | 使用自定义状态机和受控工具编排 Agent | Accepted |
| [ADR-006](0006-background-jobs.md) | 使用 Celery Beat、Redis 和数据库任务状态处理后台任务 | Accepted |
| [ADR-007](0007-pwa-frontend.md) | 使用 React + Vite 构建移动优先 PWA | Accepted |
| [ADR-008](0008-deployment-and-providers.md) | 使用 Docker、Caddy 和可替换外部服务供应商 | Accepted |

## ADR 状态

- `Proposed`：仍待确认。
- `Accepted`：作为当前实施依据。
- `Superseded`：已经被其他 ADR 替代，但保留历史。
- `Deprecated`：不再推荐，但尚未完全移除。

## 模板

```markdown
# ADR-XXX：标题

- 状态：
- 日期：
- 决策者：

## 背景

## 决策

## 备选方案

## 选择理由

## 后果和代价

## 验证方式

## 后续待办
```
