# ADR-001：采用模块化单体与 API-first 架构

- 状态：Accepted
- 日期：2026-11-22
- 决策者：项目所有者

## 背景

MyJARVIS 需要同时提供 PWA API、Agent 工具、定时任务、用户认证、多用户数据隔离和周复盘能力。当前项目由一名开发者持续开发，尚未达到需要独立部署多个服务的规模。

计划激活、任务更新、计划版本切换和通知创建需要较强的事务一致性和统一的权限校验。如果过早拆分微服务，会增加通信、部署、调试和测试成本。

## 决策

采用单仓库、模块化单体架构。

```text
PWA
  │
  ▼
FastAPI /api/v1
  │
Application Services
  ├── Domain Policies
  ├── Repositories
  ├── PostgreSQL
  ├── Redis / Celery
  └── External Adapters
```

后端按业务能力组织模块：

```text
backend/app/
├── core/
├── db/
├── auth/
├── profiles/
├── goals/
├── plans/
├── tasks/
├── reviews/
├── notifications/
├── conversations/
├── agent/
└── integrations/
```

每个模块可以包含：

- `schemas`：请求、响应和内部数据结构。
- `models`：SQLAlchemy 持久化模型。
- `repositories`：查询和持久化封装。
- `services`：业务用例、状态转换和事务边界。
- `policies`：权限和状态校验。
- `router`：HTTP 接口。

模块之间通过 application service 交互，不直接调用其他模块的 router。

## 关键规则

1. REST API 和 Agent 工具复用同一套 application service。
2. 所有业务写入都经过 service 和 policy，不直接通过 ORM 修改状态。
3. PostgreSQL 是唯一业务事实来源。
4. Redis 只承担缓存和任务传递，不保存唯一业务状态。
5. 外部模型、搜索和通知供应商通过 adapter 隔离。
6. 模块可以拆分，但必须由真实容量或团队边界触发，而不是为了形式上的“分布式”。

## 备选方案

### 微服务

优点是服务边界明确、可独立扩容；缺点是当前数据量小、团队规模小，会显著增加事务、部署和调试复杂度。

### Serverless 单函数

优点是按需运行；缺点是 Agent 长任务、后台 Worker、数据库连接和 PWA API 的组合调试困难。

### Django 单体

可以快速获得认证、后台和 ORM，但当前项目已经基于 FastAPI 建设，且 Agent API、异步 SQLAlchemy 和 SSE 更适合继续使用 FastAPI。

## 后果和代价

- 一个部署单元承载多个业务模块，需要严格遵守模块边界。
- 单模块变更可能影响完整服务，必须通过 CI、测试和清晰依赖约束降低风险。
- 无法通过“服务数量”展示架构，但可以通过领域边界、工具安全、可靠任务和测试质量展示工程能力。

## 验证方式

- 任意业务功能都从明确的模块入口进入。
- API 与 Agent 工具调用相同的业务 service。
- 不存在跨模块直接修改数据库模型的实现。
- 核心流程可以在一个本地 Docker 环境中完整运行。

## 后续待办

- 在 P1 中建立目录结构和依赖约束。
- 在 P4 中明确各模块 application service。
- 当单模块吞吐或团队规模出现真实瓶颈时，再新增拆分 ADR。
