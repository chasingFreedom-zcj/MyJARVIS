# MyJARVIS API 契约

本文件定义 PWA、用户操作和 Agent 运行所依赖的 API 边界。

API 契约必须以以下文档为依据：

- `docs/product/PRODUCT_SPEC.md`
- `docs/domain/DOMAIN_MODEL.md`
- `docs/domain/LIFECYCLE.md`
- `docs/agent/AGENT_POLICY.md`

本文件只定义接口和业务契约，不规定具体框架实现。

## 1. API 设计原则

### 1.1 查询和命令分开

- 查询接口只读取数据。
- 命令接口表达明确的业务动作，例如“激活计划”“批准变更”。
- 不通过普通 `PATCH /plans/{id}` 任意修改状态和关键字段。
- 每个命令都必须校验当前状态、用户权限和业务前置条件。

推荐：

```text
POST /plans/{id}/activate
POST /plans/{id}/pause
POST /plans/{id}/resume
POST /plans/{id}/complete
POST /plans/{id}/cancel
```

不推荐：

```text
PATCH /plans/{id}
{"status": "ACTIVE"}
```

显式命令能让权限、状态转换、事务和副作用更清楚。

### 1.2 API 不是数据库表映射

用户更新任务进度时，不直接修改任务状态字段，而是提交一次跟进：

```text
POST /plans/{plan_id}/check-ins
```

后端负责：

```text
创建 CheckIn
→ 追加 TaskUpdate
→ 更新 Task 当前状态和进度
→ 重新计算 Milestone
→ 检查计划是否具备完成条件
```

历史记录不能被静默覆盖。

### 1.3 API 和 Agent 工具复用同一套业务服务

Agent 不通过内部 HTTP 调用自己的 REST API。

```text
PWA / 用户 API ─┐
                 ├─→ Application Services → Domain / Database
Agent Tool ─────┘
```

REST 路由和 Agent 工具执行器调用相同的 application service，避免同一个业务规则在不同入口下出现不一致。

### 1.4 用户专属操作不能由 Agent 调用

以下接口只能由当前用户通过认证后调用：

- 激活计划。
- 批准或拒绝关键计划变更。
- 确认或拒绝画像洞察。
- 完成或取消目标。
- 删除业务数据。
- 修改安全设置。

这些接口不能注册为 Agent 工具。

### 1.5 写操作必须支持幂等

所有重要写请求支持：

```http
Idempotency-Key: <unique-client-request-id>
```

计划结构变更还必须携带基准版本：

```text
base_version_id
```

同一幂等键重复提交时，应返回第一次成功结果，不能产生重复跟进、重复计划版本或重复通知。

## 2. 通用约定

### 2.1 路径和版本

统一前缀：

```text
/api/v1
```

MVP 暂时只维护一个业务版本，但保留路径版本以支持后续演进。

### 2.2 身份和授权

- 当前用户身份来自认证上下文。
- 客户端不能通过请求体提交 `user_id` 访问其他用户的数据。
- 所有资源访问都在 application service 中校验所有权。
- 无权限访问其他用户资源时，默认返回 `404` 或 `403`，不能泄漏资源是否存在。

### 2.3 时间

- 服务端时间使用 ISO 8601 UTC 字符串。
- 示例：`2026-11-22T08:00:00Z`。
- 用户本地时区单独保存。
- 通知和免打扰时间使用用户时区解释。

### 2.4 标识符

- API 暴露的 ID 对客户端是不透明字符串。
- 前端不能依赖 ID 的递增规律或内部数据库类型。
- Agent 和 API 都使用服务端返回的稳定 ID 关联资源。

### 2.5 分页

列表接口使用游标分页：

```http
GET /api/v1/goals?limit=20&cursor=...
```

响应：

```json
{
  "items": [],
  "next_cursor": null
}
```

消息、通知、复盘和 Agent 运行事件等可能持续增长的数据必须分页或使用游标拉取。

### 2.6 错误响应

统一使用 Problem Details 风格：

```json
{
  "type": "https://myjarvis.local/problems/version-conflict",
  "title": "计划版本已经变化",
  "status": 409,
  "code": "VERSION_CONFLICT",
  "detail": "请基于最新计划版本重新提交变更",
  "request_id": "req_123",
  "field_errors": []
}
```

错误码至少包含：

- `UNAUTHORIZED`
- `FORBIDDEN`
- `RESOURCE_NOT_FOUND`
- `INVALID_ARGUMENT`
- `INVALID_STATE`
- `VERSION_CONFLICT`
- `CONFIRMATION_REQUIRED`
- `RATE_LIMITED`
- `UPSTREAM_FAILED`
- `INTERNAL_ERROR`

### 2.7 状态码

| 状态码 | 用途 |
|---|---|
| `200` | 查询或普通命令成功 |
| `201` | 创建资源成功 |
| `202` | 已接受异步 Agent、通知或复盘任务 |
| `204` | 删除成功且无响应体 |
| `400` | 请求格式不合法 |
| `401` | 未登录或认证失效 |
| `403` | 已登录但无权执行该操作 |
| `404` | 资源不存在或当前用户无权查看 |
| `409` | 状态冲突、版本冲突或重复资源 |
| `422` | 业务校验失败 |
| `429` | 触发限流 |
| `502` | 外部模型、搜索或邮件服务失败 |
| `503` | 服务暂时不可用 |

### 2.8 OpenAPI 要求

- 所有请求和响应使用明确的 Schema。
- 禁止使用任意结构替代已定义的业务对象。
- 枚举值必须与领域生命周期一致。
- OpenAPI 文档需要能够生成 TypeScript 客户端。
- 接口变更必须同步更新本文档和验收场景。

## 3. 认证与用户

认证具体方式仍可在架构决策阶段确认，接口职责保持如下。

| 方法 | 路径 | 功能 | 权限 |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | 注册账号 | 访客 |
| `POST` | `/api/v1/auth/login` | 登录 | 访客 |
| `POST` | `/api/v1/auth/refresh` | 刷新会话 | 有效刷新会话 |
| `POST` | `/api/v1/auth/logout` | 注销当前会话 | 已登录用户 |
| `GET` | `/api/v1/me` | 获取当前用户摘要 | 已登录用户 |
| `PATCH` | `/api/v1/me` | 修改昵称、时区等基础信息 | 已登录用户 |

`GET /me` 至少返回：

- 用户 ID。
- 显示名称。
- 时区。
- 当前画像摘要。
- 当前目标和生效计划数量。
- 未处理确认数量。

认证失败不能泄漏可用于账号枚举的内部细节。

## 4. 用户画像

### 4.1 当前画像和画像事实

| 方法 | 路径 | 功能 | 权限 |
|---|---|---|---|
| `GET` | `/api/v1/me/profile` | 获取当前生效画像 | 当前用户 |
| `GET` | `/api/v1/me/profile/facts` | 查询画像事实和来源 | 当前用户 |
| `POST` | `/api/v1/me/profile/facts` | 用户主动添加画像事实 | 当前用户 |
| `PATCH` | `/api/v1/me/profile/facts/{fact_id}` | 修改并产生替代记录 | 当前用户 |
| `POST` | `/api/v1/me/profile/facts/{fact_id}/confirm` | 确认待确认事实 | 当前用户 |
| `POST` | `/api/v1/me/profile/facts/{fact_id}/reject` | 拒绝待确认事实 | 当前用户 |
| `DELETE` | `/api/v1/me/profile/facts/{fact_id}` | 删除画像事实 | 当前用户 |

### 4.2 添加画像事实

```http
POST /api/v1/me/profile/facts
Idempotency-Key: profile-fact-123
```

```json
{
  "category": "AVAILABILITY",
  "key": "weekly_hours",
  "value": 8,
  "source": {
    "type": "USER_FORM"
  }
}
```

用户直接填写且含义明确的信息可以进入 `CONFIRMED`。从模糊对话中提取的信息应进入 `PENDING_CONFIRMATION`。

### 4.3 删除规则

画像事实删除后：

- 不再参与当前画像和个性化。
- 状态进入 `DELETED`。
- 后续计划不能把该事实作为当前依据。
- 必要审计信息是否保留由隐私策略决定。

## 5. 候选洞察

| 方法 | 路径 | 功能 | 权限 |
|---|---|---|---|
| `GET` | `/api/v1/me/profile/insights` | 查询候选、待确认和历史洞察 | 当前用户 |
| `GET` | `/api/v1/me/profile/insights/{insight_id}` | 查看洞察、证据和评分明细 | 当前用户 |
| `POST` | `/api/v1/me/profile/insights/{insight_id}/confirm` | 确认洞察并加入画像 | 当前用户专属 |
| `POST` | `/api/v1/me/profile/insights/{insight_id}/reject` | 拒绝洞察 | 当前用户专属 |
| `POST` | `/api/v1/me/profile/insights/{insight_id}/use-for-plan` | 仅用于当前计划 | 当前用户专属 |
| `DELETE` | `/api/v1/me/profile/insights/{insight_id}` | 删除洞察记录 | 当前用户 |

### 5.1 查询过滤

`GET /me/profile/insights` 支持：

```text
status=SUPPORTED
status=CONFIRMATION_REQUESTED
status=USER_CONFIRMED
scope=profile
scope=plan
limit=20
cursor=...
```

默认不返回 `CANDIDATE`，除非用户主动查看全部候选。

### 5.2 确认洞察

```http
POST /api/v1/me/profile/insights/insight_123/confirm
Idempotency-Key: insight-confirm-123
```

成功后：

- `ProfileInsight` 从 `CONFIRMATION_REQUESTED` 变为 `USER_CONFIRMED`。
- 创建或更新对应 `ProfileFact`。
- 保存洞察与画像事实的来源关系。
- 返回用户可以继续编辑的正式画像事实。

### 5.3 仅用于计划

```json
{
  "plan_id": "plan_123"
}
```

该操作：

- 不创建正式 `ProfileFact`。
- 只对指定计划的个性化产生作用。
- 必须记录用户明确选择。

确认和拒绝洞察不能作为 Agent 工具调用。

## 6. 目标

| 方法 | 路径 | 功能 |
|---|---|---|
| `POST` | `/api/v1/goals` | 创建目标 |
| `GET` | `/api/v1/goals` | 查询当前用户目标 |
| `GET` | `/api/v1/goals/{goal_id}` | 查询目标详情 |
| `PATCH` | `/api/v1/goals/{goal_id}` | 修改标题、说明等非状态字段 |
| `POST` | `/api/v1/goals/{goal_id}/pause` | 暂停目标 |
| `POST` | `/api/v1/goals/{goal_id}/resume` | 恢复目标 |
| `POST` | `/api/v1/goals/{goal_id}/complete` | 确认完成目标 |
| `POST` | `/api/v1/goals/{goal_id}/cancel` | 取消目标 |

### 6.1 创建目标

```json
{
  "title": "两个月内开始投递数据分析岗位",
  "desired_outcome": "具备可投递的数据分析项目、简历和面试准备",
  "constraints": "每周可投入 8 小时",
  "start_date": "2026-11-23",
  "deadline": "2027-01-18"
}
```

目标创建后进入 `ACTIVE`。

### 6.2 状态命令

- 已取消或已完成的目标不能普通恢复。
- 暂停目标需要暂停关联计划和跟进。
- 完成目标前必须处理未完成任务。

## 7. 计划与版本

### 7.1 创建和查询

| 方法 | 路径 | 功能 |
|---|---|---|
| `POST` | `/api/v1/goals/{goal_id}/plans` | 创建计划草稿 |
| `GET` | `/api/v1/goals/{goal_id}/plans` | 获取目标的计划列表 |
| `GET` | `/api/v1/plans/{plan_id}` | 获取计划及当前版本摘要 |
| `GET` | `/api/v1/plans/{plan_id}/versions` | 获取版本历史 |
| `GET` | `/api/v1/plans/{plan_id}/versions/{version_id}` | 获取版本结构快照 |

### 7.2 创建计划草稿

```http
POST /api/v1/goals/goal_123/plans
Idempotency-Key: plan-draft-123
```

```json
{
  "title": "数据分析岗位八周准备计划",
  "milestones": [
    {
      "title": "补齐 SQL 基础",
      "tasks": [
        {
          "title": "完成 SQL 窗口函数练习",
          "estimated_minutes": 120,
          "depends_on": []
        }
      ]
    }
  ]
}
```

成功后：

- 创建 `Plan`，状态为 `DRAFT`。
- 创建第一个 `PlanVersion`，状态为 `DRAFT`。
- 不创建跟进安排。
- 不发送提醒。

### 7.3 修改草稿

```http
PATCH /api/v1/plans/plan_123/draft
Idempotency-Key: draft-update-456
```

```json
{
  "draft_revision": 3,
  "changes": {}
}
```

要求：

- 计划仍为 `DRAFT`。
- 当前用户拥有计划。
- `draft_revision` 与最新草稿一致。
- 不允许通过该接口激活计划。

### 7.4 生命周期命令

| 方法 | 路径 | 功能 | 调用者 |
|---|---|---|---|
| `POST` | `/api/v1/plans/{plan_id}/activate` | 激活草稿 | 用户专属 |
| `POST` | `/api/v1/plans/{plan_id}/pause` | 暂停计划 | 用户 |
| `POST` | `/api/v1/plans/{plan_id}/resume` | 恢复计划 | 用户 |
| `POST` | `/api/v1/plans/{plan_id}/complete` | 确认完成 | 用户 |
| `POST` | `/api/v1/plans/{plan_id}/cancel` | 取消计划 | 用户 |

### 7.5 激活计划

```http
POST /api/v1/plans/plan_123/activate
Idempotency-Key: activation-456
```

```json
{
  "version_id": "version_1",
  "confirm": true
}
```

必须原子完成：

```text
Plan DRAFT → ACTIVE
PlanVersion DRAFT → ACTIVE
创建或激活 FollowUpSchedule
```

任何一步失败都必须回滚，计划不能单独进入 `ACTIVE`。

## 8. 计划变更

| 方法 | 路径 | 功能 | 调用者 |
|---|---|---|---|
| `POST` | `/api/v1/plans/{plan_id}/change-proposals` | 提出关键变更 | 用户或 Agent |
| `GET` | `/api/v1/plans/{plan_id}/change-proposals` | 查询变更记录 | 当前用户 |
| `GET` | `/api/v1/change-proposals/{proposal_id}` | 查看变更差异 | 当前用户 |
| `POST` | `/api/v1/change-proposals/{proposal_id}/approve` | 批准并应用 | 用户专属 |
| `POST` | `/api/v1/change-proposals/{proposal_id}/reject` | 拒绝 | 用户专属 |
| `POST` | `/api/v1/plans/{plan_id}/adjustments` | 应用低风险调整 | 用户或 Agent 工具 |

### 8.1 提出关键变更

```http
POST /api/v1/plans/plan_123/change-proposals
Idempotency-Key: proposal-789
```

```json
{
  "base_version_id": "version_2",
  "reason": "用户本周可用时间减少",
  "changes": [
    {
      "operation": "MOVE_TASK",
      "task_id": "task_10",
      "from_date": "2026-11-25",
      "to_date": "2026-11-30"
    }
  ],
  "evidence_ids": [
    "checkin_123"
  ]
}
```

后端根据实际修改内容重新判断风险等级，不信任客户端或 LLM 自报的风险等级。

### 8.2 批准变更

```http
POST /api/v1/change-proposals/proposal_789/approve
Idempotency-Key: approve-proposal-789
```

批准和应用应在同一事务中完成：

```text
校验 Proposal 和基准版本
→ 创建新 PlanVersion
→ 旧版本 SUPERSEDED
→ 新版本 ACTIVE
→ Proposal APPLIED
→ 失效其他基于旧版本的 Proposal
```

### 8.3 低风险调整

```http
POST /api/v1/plans/plan_123/adjustments
```

只有满足以下条件才允许自动应用：

- 计划为 `ACTIVE`。
- `base_version_id` 是当前版本。
- 不改变任务数量和任务集合。
- 不改变总预计用时。
- 不改变任务或阶段截止日期。
- 不改变目标范围、关键里程碑或每周投入时间。

否则返回 `409 VERSION_CONFLICT` 或 `422 CONFIRMATION_REQUIRED`。

## 9. 任务与跟进

### 9.1 任务查询

| 方法 | 路径 | 功能 |
|---|---|---|
| `GET` | `/api/v1/plans/{plan_id}/tasks` | 查询当前版本有效任务 |
| `GET` | `/api/v1/tasks/{task_id}` | 查询任务详情 |
| `GET` | `/api/v1/tasks/{task_id}/updates` | 查询任务历史更新 |

不提供普通 `PATCH /tasks/{id}` 直接修改状态和进度。任务状态来自用户跟进记录。

### 9.2 提交跟进

```http
POST /api/v1/plans/plan_123/check-ins
Idempotency-Key: checkin-123
```

```json
{
  "occurred_at": "2026-11-22T13:00:00Z",
  "available_minutes": 60,
  "note": "周三只能投入一小时",
  "task_updates": [
    {
      "task_id": "task_123",
      "reported_status": "PARTIAL",
      "progress": 50,
      "note": "项目复盘完成一半"
    },
    {
      "task_id": "task_456",
      "reported_status": "NOT_STARTED",
      "progress": 0
    }
  ],
  "source": {
    "type": "USER_FORM"
  }
}
```

`reported_status` 是用户反馈值：

- `COMPLETED`
- `PARTIAL`
- `NOT_STARTED`
- `BLOCKED`

后端映射：

- `COMPLETED` → 进度 `100%`、任务 `DONE`
- `PARTIAL` → 进度 `1%～99%`、任务 `IN_PROGRESS`
- `NOT_STARTED` → 进度 `0%`、任务 `TODO`
- `BLOCKED` → 保留当前进度、任务 `BLOCKED`

### 9.3 查询跟进

| 方法 | 路径 | 功能 |
|---|---|---|
| `GET` | `/api/v1/plans/{plan_id}/check-ins` | 查询计划跟进历史 |
| `GET` | `/api/v1/check-ins/{check_in_id}` | 查询一次完整跟进 |

一次请求中的任务更新必须整体成功或整体失败。

## 10. 周复盘

| 方法 | 路径 | 功能 |
|---|---|---|
| `POST` | `/api/v1/plans/{plan_id}/reviews` | 请求生成周期复盘 |
| `GET` | `/api/v1/plans/{plan_id}/reviews` | 查询复盘历史 |
| `GET` | `/api/v1/reviews/{review_id}` | 获取复盘内容 |
| `GET` | `/api/v1/reviews/{review_id}/insights` | 查看本次复盘产生的候选洞察 |
| `POST` | `/api/v1/reviews/{review_id}/regenerate` | 用户请求重新生成 |

### 10.1 请求复盘

```json
{
  "period_start": "2026-11-16",
  "period_end": "2026-11-22",
  "timezone": "Asia/Shanghai"
}
```

包含多个模型调用的实现建议返回：

```http
202 Accepted
```

```json
{
  "review_id": "review_123",
  "status": "GENERATING"
}
```

### 10.2 复盘与洞察

- 复盘生成失败不能改变任务、计划或画像。
- 洞察提取失败不能使已经生成完成的复盘失效。
- `GET /reviews/{review_id}/insights` 只返回关联候选洞察，不自动确认任何洞察。

## 11. 通知与提醒

| 方法 | 路径 | 功能 |
|---|---|---|
| `GET` | `/api/v1/me/notification-preferences` | 查询通知偏好 |
| `PUT` | `/api/v1/me/notification-preferences` | 更新用户通知偏好 |
| `GET` | `/api/v1/plans/{plan_id}/follow-ups` | 查询计划跟进安排 |
| `PUT` | `/api/v1/plans/{plan_id}/follow-ups/{schedule_id}` | 更新跟进节奏 |
| `POST` | `/api/v1/follow-ups/{schedule_id}/snooze` | 稍后提醒 |
| `POST` | `/api/v1/push-subscriptions` | 注册 PWA 推送端点 |
| `DELETE` | `/api/v1/push-subscriptions/{subscription_id}` | 注销推送端点 |
| `GET` | `/api/v1/notifications` | 查询站内通知 |

### 11.1 稍后提醒

```json
{
  "next_due_at": "2026-11-23T20:00:00+08:00"
}
```

该操作只修改下一次到期时间，不改变 `FollowUpSchedule` 状态。

### 11.2 PWA 推送

注册推送端点时必须校验：

- 当前用户已登录。
- 推送端点格式合法。
- 用户同意接收推送。
- 一个端点只能绑定对应用户的授权记录。

计划暂停或取消后，待发送通知必须被取消或暂停。

## 12. Agent 对话与运行

Agent 回复可能包含多次工具调用，处理时间可能超过普通 HTTP 请求，因此采用持久化运行记录加 SSE 事件流。

### 12.1 会话

| 方法 | 路径 | 功能 |
|---|---|---|
| `POST` | `/api/v1/conversations` | 创建会话 |
| `GET` | `/api/v1/conversations` | 查询会话 |
| `GET` | `/api/v1/conversations/{conversation_id}/messages` | 查询历史消息 |

### 12.2 创建 Agent 运行

```http
POST /api/v1/conversations/conversation_123/runs
Idempotency-Key: agent-run-123
```

```json
{
  "message": "根据我的情况制定一个两个月求职计划",
  "client_message_id": "client-message-123",
  "context": {
    "goal_id": "goal_456"
  }
}
```

响应：

```http
202 Accepted
```

```json
{
  "run_id": "run_789",
  "status": "RUNNING",
  "events_url": "/api/v1/agent-runs/run_789/events"
}
```

### 12.3 Agent 运行状态

建议 API 运行状态：

- `QUEUED`
- `RUNNING`
- `WAITING_FOR_USER`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `TIMED_OUT`

这些是执行状态，不替代业务对象的生命周期状态。

### 12.4 SSE 事件流

```http
GET /api/v1/agent-runs/run_789/events
Accept: text/event-stream
```

事件类型：

- `message_started`
- `token_delta`
- `tool_started`
- `tool_completed`
- `needs_user_action`
- `message_completed`
- `run_failed`

示例：

```text
event: needs_user_action
data: {"action":"APPROVE_PLAN_CHANGE","proposal_id":"proposal_123"}

event: message_completed
data: {"message_id":"message_456","run_id":"run_789"}
```

### 12.5 断线和恢复

| 方法 | 路径 | 功能 |
|---|---|---|
| `GET` | `/api/v1/agent-runs/{run_id}` | 查询运行和当前业务结果 |
| `GET` | `/api/v1/agent-runs/{run_id}/events` | 订阅或恢复事件流 |

要求：

- 客户端断开后，运行可以继续或安全结束。
- 重新连接时可以补发未接收事件。
- 已完成或已失败运行不能重新执行。
- 相同幂等键不会创建重复 Agent 运行。

### 12.6 Agent 工具边界

API 不暴露任意工具执行接口。客户端不能提交“调用某个 Agent 工具”的请求。工具只能由后端 Agent 编排器根据受控注册表和当前用户权限执行。

## 13. 关键请求和响应示例

### 13.1 提交任务跟进

请求：

```http
POST /api/v1/plans/plan_123/check-ins
Idempotency-Key: checkin-20261122-1
Content-Type: application/json
```

```json
{
  "occurred_at": "2026-11-22T13:00:00Z",
  "available_minutes": 60,
  "note": "项目复盘完成一半，周三只能投入一小时",
  "task_updates": [
    {
      "task_id": "task_123",
      "reported_status": "PARTIAL",
      "progress": 50
    }
  ],
  "source": {
    "type": "PWA"
  }
}
```

响应：

```http
201 Created
```

```json
{
  "check_in_id": "checkin_123",
  "task_updates": [
    {
      "task_id": "task_123",
      "status": "IN_PROGRESS",
      "progress": 50
    }
  ],
  "plan_progress": 42.5,
  "completion_ready": false
}
```

### 13.2 拒绝关键变更

```http
POST /api/v1/change-proposals/proposal_123/reject
Idempotency-Key: reject-proposal-123
```

```json
{
  "reason": "这周只是特殊情况，先不改计划"
}
```

成功后：

- Proposal 进入 `REJECTED`。
- 当前计划和版本保持不变。
- Agent 不能立即重复提出同一个调整。

### 13.3 用户确认候选洞察

```http
POST /api/v1/me/profile/insights/insight_123/confirm
Idempotency-Key: confirm-insight-123
```

成功后：

- 洞察进入 `USER_CONFIRMED`。
- 创建或更新 `ProfileFact`。
- 返回对应画像事实及来源关系。

## 14. 错误码与状态码

### 14.1 常见业务错误

| HTTP 状态 | 业务错误码 | 场景 |
|---|---|---|
| `401` | `UNAUTHORIZED` | 未登录或令牌失效 |
| `403` | `FORBIDDEN` | 已登录但无权执行 |
| `404` | `RESOURCE_NOT_FOUND` | 资源不存在或不可见 |
| `409` | `VERSION_CONFLICT` | 基准版本已过期 |
| `409` | `INVALID_STATE` | 当前对象不能执行该命令 |
| `409` | `DUPLICATE_OPERATION` | 已存在相同业务操作 |
| `422` | `CONFIRMATION_REQUIRED` | 关键变化需要用户批准 |
| `422` | `INVALID_ARGUMENT` | 请求字段不符合业务要求 |
| `429` | `RATE_LIMITED` | 请求过于频繁 |
| `502` | `UPSTREAM_FAILED` | 模型、搜索或邮件服务失败 |

### 14.2 错误不能伪装成成功

- 模型失败不能返回一个成功生成的计划。
- 工具执行失败不能返回已完成的任务更新。
- 通知失败不能返回 `SENT`。
- 复盘失败不能保存半成品为 `READY`。
- 权限或版本冲突不能被 Agent 改写为普通文字后继续执行。

## 15. API 验收场景

以下场景应成为后续集成测试和端到端测试的基础。

### 15.1 权限和身份

1. 用户不能访问其他用户的目标、计划、任务、画像、复盘和运行记录。
2. 请求体中的伪造 `user_id` 不能覆盖认证身份。
3. 其他用户的任务不能加入当前用户的跟进。
4. 其他用户的画像事实不能用于当前计划。

### 15.2 计划生命周期

1. 普通 `PATCH` 不能直接把计划状态改为 `ACTIVE`。
2. 激活计划必须显式调用激活接口。
3. 激活计划时创建跟进安排失败，整个操作回滚。
4. 已取消计划不能通过普通接口恢复。
5. 同一目标不能同时存在两个生效计划。

### 15.3 变更和并发

1. 延长截止日期的请求返回 `CONFIRMATION_REQUIRED`。
2. 用户批准 Proposal 后产生新版本，旧版本保持历史。
3. 用户拒绝后当前计划不变。
4. `base_version_id` 已过期时返回 `409 VERSION_CONFLICT`。
5. 相同幂等键重复提交不会产生多个版本。

### 15.4 跟进和进度

1. 任务进度只能通过 `CheckIn` 和 `TaskUpdate` 更新。
2. 一次跟进中任一任务非法时，整个请求回滚。
3. `COMPLETED` 更新生成 `DONE` 和 `100%`。
4. `PARTIAL` 更新生成 `IN_PROGRESS` 和对应进度。
5. 相同用户消息重复处理不会产生重复 `TaskUpdate`。

### 15.5 画像和洞察

1. 未确认的洞察不出现在当前画像。
2. 洞察确认接口只能由用户身份调用。
3. 用户确认后创建或更新 `ProfileFact`。
4. 用户拒绝后画像事实不变。
5. 洞察评分明细和证据可以通过查询接口获取。

### 15.6 复盘和通知

1. 周复盘失败不会改变任务和画像。
2. 洞察提取失败不会使已生成的复盘失效。
3. 计划暂停后不再发送新提醒。
4. 相同提醒的多个投递尝试不会变成多个逻辑提醒。

### 15.7 Agent 运行

1. Agent 运行失败不会产生虚假消息或业务写入。
2. 用户断开 SSE 后可以查询最终状态或恢复事件。
3. 相同幂等键不会创建重复运行。
4. Agent 不能通过公开 API 调用自己的用户专属审批接口。
5. Agent 工具失败时运行返回明确错误，而不是虚假成功。

## 16. P0.5 完成标准

P0.5 完成时，应同时满足：

- 产品规格中的每个用户故事都有明确 API。
- 领域对象和生命周期都有对应查询或命令入口。
- API 不能绕过计划状态机、画像确认或 Agent 风险等级。
- 用户专属审批和 Agent 工具边界明确。
- 关键命令支持幂等、版本冲突和事务回滚。
- 错误格式和状态码足以支撑前端交互。
- 接口契约可以继续转化为 OpenAPI 和自动化测试。
