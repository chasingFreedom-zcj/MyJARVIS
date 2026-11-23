# ADR-006：使用 Celery Beat、Redis 和数据库任务状态处理后台任务

- 状态：Accepted
- 日期：2026-11-22
- 决策者：项目所有者

## 背景

MyJARVIS 需要在用户关闭浏览器后继续发送跟进提醒、执行重试、生成周复盘和触发画像洞察提取。FastAPI 请求内的 `BackgroundTasks` 不能提供持久调度和可靠重试。

## 决策

采用 Celery Worker、Celery Beat 和 Redis，同时把业务任务状态保存在 PostgreSQL。

```text
API 事务
  → 保存 NotificationJob / ReviewJob
  → Redis 发布任务
  → Celery Worker 领取
  → 发送推送、邮件或执行分析
  → 更新数据库任务状态
```

数据库是任务事实来源，Redis 是调度和传输层。

## 可靠性设计

1. 业务任务先写入 PostgreSQL，再发布到 Redis。
2. 发布失败的任务由周期性扫描任务重新领取。
3. Worker 使用租约和 `FOR UPDATE SKIP LOCKED` 领取到期任务。
4. 任务保存尝试次数、下次重试时间和最终错误。
5. 每个任务有幂等键，重试不能生成重复业务记录。
6. Worker 崩溃后，租约过期的任务可以恢复。
7. 超过最大重试次数的任务进入 `FAILED_PERMANENTLY` 并告警。

## 选择理由

- Celery 支持 Worker、定时任务、重试和任务路由。
- Redis 轻量且适合任务传递。
- 数据库任务状态可以防止 Redis 丢失导致业务任务永久消失。
- 通知发送可以独立于 API 进程运行。
- Celery 在工程实践中常见，便于说明可靠任务处理能力。

## 备选方案

### FastAPI BackgroundTasks

不能保证进程重启后的任务恢复，也不适合延迟数天的提醒。

### APScheduler 单进程

适合小型定时任务，但多实例、租约和可靠性需要额外实现。

### ARQ 或其他异步队列

与 asyncio 更自然，但生态和通用工程认知度不如 Celery。若后续验证 Celery 成为明显负担，应新增 ADR。

## 后果和代价

- 本地和生产都需要管理 Redis 与 Worker。
- Celery 任务不能只依赖 Redis 中的临时状态。
- 任务序列化和版本兼容需要测试。
- 通知逻辑必须具备幂等和退避重试。

## 验证方式

- 服务重启后未到期的提醒仍能发送。
- Redis 短时不可用后，数据库扫描可以恢复待处理任务。
- 同一通知重复调度只产生一次业务提醒。
- Worker 崩溃后，租约过期任务可重新领取。
- 计划暂停后未发送通知被取消或暂停。

## 后续待办

- 在 P8 设计任务表和 Worker。
- 在部署阶段加入 Worker 健康检查和积压监控。
- 邮件和 Web Push 使用独立 adapter。
