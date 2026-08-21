# Database Design

## 1. Overview

Trident 使用 repository abstraction 隔离业务层与数据库。当前 Demo 可以使用 SQLite，面向客户的多用户版本应使用 PostgreSQL。数据库保存结构化状态和元数据，大文件应迁移至对象存储。

## 2. Current Schema

当前持久化基线以 `projects` 表保存项目索引和完整 `payload_json`：

| 字段 | 用途 |
|---|---|
| `project_id` | 项目唯一标识 |
| `project_name` | 项目名称 |
| `industry` | 行业 |
| `region` | 地区 |
| `current_step` | 当前研究节点 |
| `updated_at` | 最后更新时间 |
| `payload_json` | 当前项目完整状态 |

这一设计适合快速迁移和 Demo，但不适合长期多租户查询、局部更新和分析型使用。

## 3. Target Data Models

| 实体 | 说明 |
|---|---|
| Tenant / Workspace | 客户组织与数据隔离边界 |
| User / Membership / Role | 用户、成员关系和权限 |
| Project | 项目元信息、场景、状态和负责人 |
| ResearchBrief / Plan / Task | 研究需求、任务与执行状态 |
| Source / Evidence / Citation | 来源、证据陈述、采用状态与引用 |
| Artifact / ArtifactVersion | 分析、趋势、报告、评分和行动计划版本 |
| EnterpriseProfile | 企业画像、战略意图和决策风格 |
| EnterpriseDocument | 文件元数据、敏感级别、审核状态和对象地址 |
| ScoreDimension / Score | 动态维度、公司分、市场分、目标分和置信度 |
| Action / ProgressUpdate | 行动、责任人、时点、状态和反馈 |
| SensingSignal | 政策、新闻、公司与市场信号 |
| Conversation / Message | 访谈、审阅与长期交互记录 |
| AuditEvent / UsageRecord | 审计、模型调用与成本记录 |

## 4. Relationships

- Tenant 1:N Projects、Users、EnterpriseProfiles。
- Project 1:1 ResearchBrief，1:N Tasks、Evidence、Artifacts、Reviews。
- Artifact 1:N ArtifactVersions，版本记录父子关系。
- EnterpriseProfile 1:N Documents、Scorecards、ActionPlans。
- Scorecard 1:N Dimensions；Action Plan 引用 Scorecard Gap 与战略目标。
- SensingSignal 可关联多个项目、企业或投资标的。

## 5. Naming Conventions

- 表名和字段名使用 `snake_case`。
- 主键使用稳定的 UUID/ULID，不使用业务名称。
- 时间字段统一 `*_at`，使用 UTC 保存。
- 外键统一 `<entity>_id`。
- 状态字段使用受控枚举，未知值必须有兼容策略。

## 6. Indexing

优先索引：`tenant_id`、`project_id`、`updated_at`、`status`、`source_url_hash`、`artifact_type`、`parent_version_id`。全文检索和向量检索应使用独立索引，不把高维向量塞入普通 JSON 查询路径。

## 7. Migration Strategy

1. 保持 repository 接口稳定。
2. 先将 SQLite `payload_json` 数据迁移至 PostgreSQL 同构表。
3. 再按访问频率拆出 tasks、evidence、artifacts 和 audit_events。
4. 每次 schema 变更使用 Alembic migration。
5. 迁移脚本必须支持 dry-run、校验数量与回滚。

## 8. Retention

- 项目、报告、审阅记录：按客户合同保留。
- 临时抓取正文与中间模型输出：设置较短生命周期。
- 已删除企业文件：软删除后进入可恢复期，到期物理删除。
- 审计日志：不可由普通项目用户修改。

## 9. Backup and Recovery

- Demo SQLite：持久卷每日快照，单实例写入。
- SaaS PostgreSQL：自动备份、时间点恢复、跨区副本按等级启用。
- 定期执行恢复演练，而不仅是确认“备份成功”。

## 10. Security

- 所有业务表必须包含租户边界。
- PostgreSQL 使用 RLS 或等价服务层隔离。
- 连接串只存入部署平台 Secret，不进入仓库、日志或前端。
- 企业原始文件与解析文本分级授权。
- 高敏字段根据需求使用字段级加密或客户密钥。

## 11. Demo Fallback Rule

当 `DATABASE_URL` 暂不可用时，融资 Demo 可显式配置 `TRIDENT_DATABASE_MODE=sqlite` 与持久化路径。生产环境不得静默退回 SQLite；若确需 Demo fallback，页面和运维文档必须明确单实例、并发与数据持久性限制。
