# Trident 产品化系统架构路线

## 结论

Trident 可以并且应该继续使用 Web 作为客户入口；“Web”与“系统”不是二选一。客户看到的是浏览器中的 SaaS 产品，背后则从当前同步 Demo 演进为可恢复、可审计、可多租户的研究工作流系统。

最适合 Trident 的目标形态是：`Next.js Web + FastAPI API + Durable Workflow + Python Workers + PostgreSQL + Object Storage + Identity/RBAC + Observability`。Vercel 继续承载 Web/BFF，不承担整份行业研究的长任务执行。

## 为什么不能把完整研究留在一次 Web 请求

Trident 的研究任务包含多次模型调用、网页检索、抓取、人工 Gate、失败重试和可能长时间等待。Vercel Functions 有明确单次执行时限；完整研究应提交为 Job，由后台工作流异步执行，浏览器通过状态查询或事件流获得进度。这样关闭网页、重新部署或 Worker 重启后，任务仍能从持久化检查点恢复。

## 推荐的逻辑架构

```text
Browser / Mobile Web
        |
Next.js on Vercel (UI, BFF, session)
        |
API Gateway / FastAPI
        |
Durable Workflow Orchestrator
   |          |          |
Research   Search &    Report
Workers    Crawl       Export Workers
   |          |          |
PostgreSQL + Object Storage + Redis/Cache
        |
Telemetry / Audit / Error Monitoring
```

### 组件职责

- **Next.js/Vercel**：客户工作台、项目管理、报告查看、审批界面、会话和轻量 BFF。
- **FastAPI**：稳定领域 API、鉴权、租户边界、命令提交、产物查询和 Webhook。
- **Durable Workflow**：管理研究状态机、重试、超时、人工等待、取消、版本和恢复。
- **Python Workers**：运行 Prompt Analysis、搜索抓取、专业 Skill、分析、预测和报告生成。
- **PostgreSQL**：组织、用户、项目、工作流、审核决定、结构化产物和 Telemetry；所有业务表带 `organization_id`。
- **Object Storage**：用户文件、抓取快照、Word/PDF、图表和大体积中间产物。
- **Identity/RBAC/RLS**：组织管理员、研究者、审阅者、客户只读和内部产品运营角色。
- **Observability**：Token、成本、耗时、失败、重试、模型/Skill 版本和审计日志。

## 分阶段方案

### 0–1 个月：完整 Demo

- 保留 Vercel Web 与现有 FastAPI。
- 把两条研究路径全部跑通，并将每个节点改为可重复、可恢复命令。
- PostgreSQL 替换临时 SQLite；报告和文件进入对象存储。
- 当前逐任务网页研究是后台 Job 化前的过渡，不再新增超长同步接口。
- 审阅式完整初稿已采用 FastAPI 后台任务 + 项目状态轮询，避免 Vercel 单请求超时；该实现用于 Demo，进程重启恢复能力仍由后续 Durable Workflow 补齐。

### 2–5 个月：产品化与限定服务

- 上线身份、组织、成员、项目角色和邀请流程。
- FastAPI 与 Worker 部署在长期运行的托管容器；Vercel 只运行 UI/BFF。
- 使用 Durable Workflow 管理“研究—Gate—继续”的长期状态。早期可用数据库 Job + Worker 过渡，但正式付费客户前应完成工作流编排。
- 建立用量配额、计费事件、版本化 Skill/Prompt、操作审计和数据导出/删除能力。
- 用独立 Staging 和 Production 环境，完成备份恢复和故障演练。

### 5–12 个月：企业 SaaS 与选择性服务

- 多租户 PostgreSQL 开启 RLS，默认拒绝跨组织数据访问。
- Scenario Pack、FDE 服务配置、企业资料连接器和组织级知识库形成插件边界。
- 增加队列优先级、并发配额、模型路由、成本策略、SLA 和客户管理员后台。
- 海外与中国线路共享领域合同、Skill 和测试，但数据库、对象存储、模型与搜索供应商区域化部署。

### 12–24 个月：私有化系统与实施服务

- 提供容器化安装包、Helm Chart、配置模板、离线/专网模型连接器和升级迁移工具。
- 企业侧可采用 Kubernetes 管理无状态 API/Worker、定时任务和滚动升级；数据库和对象存储优先使用客户已有托管服务。
- 建立 SSO/SAML/OIDC、KMS、审计导出、数据保留、灾备和实施验收体系。
- 私有化版本仍与 SaaS 共用 Research Core，不复制一套业务代码。

## 推荐选型

| 层 | 近期推荐 | 规模化/私有化 |
|---|---|---|
| Web | Next.js + Vercel | Next.js 容器或客户 Ingress |
| API | FastAPI 托管容器 | FastAPI Deployment |
| 工作流 | Temporal Cloud；短期可数据库 Job 过渡 | Temporal 自托管或云厂商工作流 |
| Worker | Python 容器 | Kubernetes Deployment/Job |
| 数据库 | 托管 PostgreSQL | 区域 PostgreSQL/客户数据库 |
| 缓存 | 托管 Redis | 区域 Redis |
| 文件 | S3 兼容对象存储 | 客户对象存储/私有 Bucket |
| 身份 | 托管 OIDC 身份服务 | 企业 SSO + SCIM |
| 监测 | Trident Telemetry + Sentry/日志 | 区域日志、指标和审计平台 |

## 当前不建议做的事

- 不把所有后端逻辑迁入 Vercel Functions。
- 不因“系统化”立刻制作原生桌面客户端；响应式 Web/PWA 足以覆盖主要客户场景。
- 不在 0–5 个月阶段先自建 Kubernetes；它解决基础设施规模问题，不解决研究流程可靠性和产品权限问题。
- 不为海外、中国、SaaS 和私有化复制四套 Research Core；差异必须收敛在 Provider、部署配置和基础设施适配层。
