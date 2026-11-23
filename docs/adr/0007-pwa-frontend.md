# ADR-007：使用 React + Vite 构建移动优先 PWA

- 状态：Accepted
- 日期：2026-11-22
- 决策者：项目所有者

## 背景

用户主要使用 iPhone，希望先完成 Web/PWA，再评估 Capacitor 封装。产品需要聊天、计划、任务、画像、复盘和通知设置，但没有公开 SEO 页面或服务端渲染需求。

## 决策

前端采用：

- React + TypeScript。
- Vite。
- React Router。
- TanStack Query。
- Zustand，仅在确有必要时管理本地 UI 状态。
- React Hook Form + Zod。
- Tailwind CSS + Radix UI。
- `vite-plugin-pwa` 和 Service Worker。
- 原生 Fetch/EventSource 处理 SSE。
- OpenAPI 生成的 TypeScript API 类型。

## 选择理由

- Vite 对纯 PWA 构建和部署更直接，不引入 Next.js 服务端运行时。
- React 生态适合复杂表单、对话流和计划视图。
- TanStack Query 适合管理服务端状态、缓存和错误恢复。
- Zod 可以在表单层提供即时反馈，后端 Pydantic 仍是最终业务校验。
- `vite-plugin-pwa` 可以生成 Manifest、离线壳和更新提示。
- SSE 比 WebSocket 更适合单向 Agent 事件流。

## 移动端约束

1. 所有页面首先按 iPhone 安全区和触控尺寸设计。
2. 不以桌面后台布局为基础再缩小。
3. PWA 必须在 HTTPS 下运行。
4. iPhone 推送要求用户安装 PWA 并授权通知。
5. 浏览器后台能力不能作为提醒可靠性唯一依赖。
6. 推送失败必须由邮件或站内消息兜底。
7. 离线只缓存必要外壳和只读数据，不能把前端缓存作为业务真相。

## 备选方案

### Next.js

适合 SEO、服务端渲染和全栈路由，但本项目主要是登录后的交互式 PWA，SSR 会增加部署和认证复杂度。

### 原生 React Native

适合完全原生体验，但当前先做完整 Web/PWA，React Native 页面无法直接复用。后续优先通过 Capacitor 封装。

## 后果和代价

- 需要自己保证路由、认证和离线更新策略。
- iPhone Web Push 和后台行为需要真机测试。
- 以后封装 App 时需要通过 adapter 处理认证、通知、深链接和本地存储差异。

## 验证方式

- iPhone 可以将 PWA 安装到桌面。
- 核心页面无横向溢出并适配安全区。
- 离线后恢复网络可以重新获取业务数据。
- SSE 断线后可以恢复运行状态。
- 用户拒绝通知权限时仍可通过邮件完成跟进。

## 后续待办

- 在 P5 建立 React/PWA 基线。
- 在 P9 完成完整移动端体验。
- 在后续通过独立 ADR 决定 Capacitor 封装。
