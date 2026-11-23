# ADR-008：使用 Docker、Caddy 和可替换外部服务供应商

- 状态：Accepted
- 日期：2026-11-22
- 决策者：项目所有者

## 背景

MyJARVIS 需要 HTTPS PWA、FastAPI、PostgreSQL、Redis、Celery Worker、模型、搜索、邮件和 Web Push。项目需要先在本地完整运行，再部署到公网进行简历演示。

## 决策

本地和生产基础部署采用：

- Docker Compose。
- Linux VPS。
- Caddy 反向代理与自动 HTTPS。
- React 静态资源由 Caddy 或 Nginx 提供。
- FastAPI 运行在独立应用容器。
- PostgreSQL 使用托管服务或带持久卷的容器。
- Redis 与 Celery Worker 独立运行。
- GitHub Actions 执行检查和部署。
- Mailpit 作为本地邮件测试服务。
- Web Push 使用 VAPID。
- 搜索使用 adapter，初始候选为 Tavily。
- 生产邮件使用 SMTP 兼容供应商，通过环境变量配置。

外部供应商都必须通过 adapter 隔离，业务代码不能直接依赖某个供应商 SDK 的数据结构。

## 选择理由

- Docker 能保证本地、CI 和生产依赖一致。
- Caddy 可以自动申请和续期 HTTPS 证书，降低 PWA 部署门槛。
- 单台 VPS + 容器适合当前用户量，成本和行为可控。
- 外部搜索和邮件供应商可能因网络、成本和可用性变化而替换。
- SMTP adapter 可以在阿里云邮件、Resend、Mailgun 等供应商之间切换。
- VAPID 是标准 Web Push 方案，不依赖特定推送 SaaS。

## 外部供应商选择

### 搜索

初始候选：Tavily。

备选：

- Brave Search。
- Serper。
- 其他支持结构化结果和来源引用的搜索 API。

在 P7 前应做网络可达性、价格、中文搜索质量和引用完整性的集成验证。如果 Tavily 不满足条件，只需替换 adapter。

### 邮件

本地使用 Mailpit。

生产使用 SMTP 兼容供应商，优先选择在目标部署地区投递稳定、支持自定义域名和退信处理的服务。

### 模型

初始使用 DeepSeek OpenAI 兼容接口。

`LLMProvider` 需要支持超时、重试、结构化输出和用量记录，以便未来替换或增加降级模型。

### Web Push

采用 VAPID Web Push。iOS 上必须安装 PWA、用户授权且从主屏幕启动，实际能力需要真机验证。

## 部署拓扑

```text
Internet
  │
  ▼
Caddy :443
  ├── / → React PWA 静态资源
  └── /api → FastAPI
                 ├── PostgreSQL
                 ├── Redis
                 └── Celery Worker
```

## 安全和运维要求

1. 外部密钥不进入 Git。
2. 生产环境使用独立 `.env` 或密钥管理服务。
3. PostgreSQL 不直接暴露公网。
4. Caddy 和容器只开放必要端口。
5. 数据库迁移在部署应用新版本前执行。
6. 部署前自动备份数据库。
7. 健康检查覆盖 API、数据库、Redis 和 Worker。
8. 记录模型、搜索和通知失败率。
9. 配置 HTTPS、Secure Cookie 和合理 CORS。
10. 具备数据库恢复和版本回滚说明。

## 备选方案

### Railway、Render 等 PaaS

部署更快，但免费额度、网络可达性、Worker 和持久数据库成本需要在实施前验证。

### 多区域 Kubernetes

对当前项目规模明显过度，增加运维和成本。

### 完全 Serverless

长时间 Agent 运行、后台 Worker 和数据库连接管理不适合作为第一版方案。

## 后果和代价

- VPS 和域名需要基础运维。
- Celery Worker、Redis 和 PostgreSQL 需要监控与备份。
- 外部供应商的可用性和网络状况会影响产品体验。
- PWA 必须通过真实 HTTPS 域名测试。

## 验证方式

- 本地一条命令启动完整服务。
- 公网 HTTPS 可以安装 PWA。
- 生产环境不暴露数据库端口和密钥。
- 搜索供应商不可用时系统不会编造来源。
- 邮件发送失败时会尝试备用渠道并记录失败。
- CI 能运行测试和构建镜像。

## 后续待办

- 在 P1 创建本地 Docker Compose。
- 在 P7 完成搜索供应商集成验证。
- 在 P11 完成域名、HTTPS、监控、备份和演示部署。
