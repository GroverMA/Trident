# API Reference and Conventions

## 1. Overview

FastAPI 是 Trident 的业务边界。网页、未来插件、企业门户和自动化工作流均通过 API 访问同一研究状态，避免把核心逻辑绑定在某个前端框架中。

当前 API 标题为 `Trident Research API`，版本基线为 `0.3.0`。

## 2. Authentication

- **当前 Demo**：部署环境可暂不开放完整多用户认证。
- **标准 SaaS**：Bearer Token / Session，强制 tenant context。
- **企业部署**：SSO/OIDC/SAML，经 API Gateway 验证身份与权限。
- 服务端密钥不得由浏览器直接持有。

## 3. Current Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | 进程健康检查 |
| GET | `/ready` | 数据库和依赖就绪检查 |
| GET | `/v1/capabilities` | 返回当前能力和部署模式 |
| POST | `/v1/projects/{project_id}/evidence` | 按已确认 Research Plan 执行检索并保存 Evidence Matrix |
| PATCH | `/v1/projects/{project_id}/evidence` | 接受/拒绝证据并确认 Gate 1，推进至行业分析 |
| POST | `/v1/projects` | 创建项目 |
| GET | `/v1/projects` | 查询项目列表 |
| GET | `/v1/projects/{project_id}` | 查询项目详情 |
| PUT | `/v1/projects/{project_id}` | 更新完整项目 |
| DELETE | `/v1/projects/{project_id}` | 删除项目 |
| PATCH | `/v1/projects/{project_id}/scope` | 更新研究范围 |
| POST/PATCH | `/v1/projects/{project_id}/research-brief` | 生成或修改 Brief |
| POST/PATCH | `/v1/projects/{project_id}/research-plan` | 生成或修改 Plan |
| POST | `/v1/projects/{project_id}/report-first` | 执行审阅式报告初稿流程 |

## 4. Project Create Request

主要字段包括：

- `project_name`
- `industry`
- `region`
- `objective`
- `horizon`
- `language`
- `target_company`
- `company_strategy`
- `decision_context`
- `research_mode` / `research_path`
- `industry_pack`

新增字段应尽量可选并提供默认值，以兼容历史项目快照。

## 5. Response Convention

- 成功响应返回结构化对象，不把调试文本混入业务字段。
- 长任务创建后应返回 `job_id`、`status` 和轮询/事件地址。
- Artifact 返回 `artifact_id`、`version`、`status`、`created_at` 与可审计元数据。
- 错误响应包含稳定 `code`、用户可理解的 `message` 和可选 `request_id`。

## 6. Error Codes

| HTTP | Example Code | Meaning |
|---|---|---|
| 400 | `invalid_request` | 输入格式或业务字段不合法 |
| 401 | `unauthenticated` | 未登录或凭证无效 |
| 403 | `forbidden` | 无项目或租户权限 |
| 404 | `project_not_found` | 项目不存在或不可见 |
| 409 | `state_conflict` | 当前节点不允许该操作 |
| 422 | `artifact_validation_failed` | 结构化产物未通过校验 |
| 429 | `rate_limited` | 超出请求或模型预算 |
| 502 | `provider_failed` | 模型或搜索供应商失败 |
| 503 | `dependency_unavailable` | 数据库、Worker 或上游未就绪 |

## 7. Versioning

- 对外路径使用 `/v1`。
- 非破坏性字段可在 v1 增加。
- 删除/改名字段或改变状态语义时发布新版本。
- Artifact 内容版本与 API 版本分开管理。

## 8. Rate Limits and Budgets

按租户、用户、项目和工具类型限流。报告生成使用预算字段限制搜索次数、Token、抓取页面数与最大运行时间。达到预算后进入人工确认，而不是无限循环补检。

## 9. Idempotency

创建报告、运行研究和写入版本等操作应支持 `Idempotency-Key`。重复请求返回原任务状态，避免浏览器重试导致重复成本和版本。

## 10. Planned API Areas

- Jobs / Events / Streaming progress。
- Enterprise documents and review。
- Evidence selection and reference check。
- Module-level revision and review conversation。
- Scorecard and Action Plan。
- Sensing subscriptions and signals。
- Tenant, membership and role administration。
