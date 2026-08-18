# 完整研究流程迁移矩阵

## 目标

把历史 Streamlit 编排迁入共享的 Application Service、FastAPI 和 Next.js 工作台。Vercel
海外版与腾讯云大陆版从同一提交构建并使用同一流程；Streamlit 只作为回归参照，不再承载
新功能真相。

## 迁移原则

1. 业务状态和人工 Gate 位于领域/Application 层，不由页面临时状态决定。
2. 每个阶段必须保存输入、产物、状态和人工决定，刷新或区域切换不得丢失。
3. FastAPI 是统一业务边界，Next.js 与未来客户端只调用 API，不直接编排研究服务。
4. 长任务当前可同步迁移以恢复功能闭环，随后统一迁往可恢复 Job/Worker。
5. 每一批迁移同时通过共享测试、Vercel 构建和 CloudBase 镜像构建。

## 当前矩阵

| 阶段 | Application/FastAPI | Next.js | 持久化/测试 | 状态 |
|---|---|---|---|---|
| 项目与研究路径 | 已迁移 | 已迁移 | 已覆盖 | 完成 |
| Gate 0 / Research Brief | 已迁移 | 已迁移 | 已覆盖 | 完成 |
| Research Plan | 已迁移 | 已迁移 | 已覆盖 | 完成 |
| 网页检索与 Evidence Matrix | 已迁移 | 已迁移 | 已覆盖 | 完成（第一批） |
| Gate 1 证据接受/拒绝 | 已迁移 | 已迁移 | 已覆盖 | 完成（第一批） |
| Industry Analysis | 服务已存在，API 待迁移 | 待迁移 | 服务测试已有 | 下一批 |
| Future Intelligence | 服务已存在，API 待迁移 | 待迁移 | 服务测试已有 | 待迁移 |
| Gate 2 内容审核 | 规则已存在，API 待迁移 | 待迁移 | 部分覆盖 | 待迁移 |
| General Report | 服务已存在，审阅式流水线可用 | 待迁移 | 服务测试已有 | 待迁移 |
| Enterprise Sensing | 服务与旧 UI 已存在 | 待迁移 | 部分覆盖 | 待迁移 |
| Company Scorecard | 服务已存在 | 待迁移 | 服务测试已有 | 待迁移 |
| Action Plan | 服务已存在 | 待迁移 | 服务测试已有 | 待迁移 |
| Enterprise Report | 服务已存在 | 待迁移 | 服务测试已有 | 待迁移 |
| 模块级审阅与版本 | 服务已存在 | 待迁移 | 服务测试已有 | 待迁移 |
| Word/PDF 导出 | 服务已存在 | 待迁移 | 视觉与双区域验收待补 | 待迁移 |
| 异步 Job/恢复 | 尚未统一 | 进度 UI 待迁移 | 待建立 | P0 基础设施 |

## 第一批接口

- `POST /v1/projects/{project_id}/evidence`：执行一个或全部 Research Plan 任务，持久化
  搜索、抓取和结构化证据结果。
- `PATCH /v1/projects/{project_id}/evidence`：保存 Evidence 接受/拒绝决定；确认 Gate 1 后
  将项目推进至 Industry Analysis。

## 后续实施顺序

1. Industry Analysis 生成、Finding 审核与确认。
2. Future Intelligence 生成、趋势/情景审核与 Gate 2。
3. General Report 生成、内容版本和 Word/PDF 导出。
4. Enterprise Sensing、Company Scorecard、Action Plan 与 Enterprise Report。
5. 模块级修订、历史版本和恢复。
6. 将同步长任务封装为持久化 Job/Worker，并为四条主路径建立双区域 E2E。
