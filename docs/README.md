# Trident 项目知识库

本目录是 Trident 的产品、研究、工程与项目交接知识库。它用于统一团队、AI 编码助手、合作方与未来算法团队对产品边界、研究标准和技术实现的理解。

> **双区域最高原则**：Vercel 海外版与腾讯云大陆版是同一个 Trident 产品，必须共用
> 同一套研究流程、功能、业务规则、API/数据契约和版本。两者只允许在部署拓扑、区域
> 基础设施、域名、密钥、数据驻留和合规配置上不同；任何迁移、修复或新增功能必须同步
> 进入两个部署目标并完成双区域验收。

## 阅读路径

| 读者 | 建议起点 | 重点文档 |
|---|---|---|
| 产品与业务负责人 | [项目上下文](00_product/PROJECT_CONTEXT.md) | 产品规格、用户旅程、业务规则、路线图 |
| 行业研究与咨询团队 | [研究哲学](01_research/RESEARCH_PHILOSOPHY.md) | 决策框架、证据标准、报告标准、提示词规则 |
| 工程与算法团队 | [系统架构](02_engineering/ARCHITECTURE.md) | Agent 工作流、数据库、API、MCP、RAG、安全、部署 |
| 项目经理与交接人员 | [交接说明](03_project/HANDOFF.md) | 决策日志、待办、变更、发布与复盘 |
| AI 编码助手 | [AI 长期记忆](04_ai/AI_MEMORY.md) | 不变量、约束、命名规范、禁区与常用命令 |

## 状态标记

- **当前**：已在仓库中实现并有代码或测试支撑。
- **过渡**：为融资 Demo 或双区域部署采用的阶段性方案。
- **规划**：为 SaaS、企业私有部署或专业算法团队预留的能力，不应对外宣称已完成。

## 目录

### 00_product

- [PROJECT_CONTEXT.md](00_product/PROJECT_CONTEXT.md)：项目背景、愿景、边界与成功指标。
- [PRODUCT_SPEC.md](00_product/PRODUCT_SPEC.md)：产品功能与验收口径。
- [USER_PERSONAS.md](00_product/USER_PERSONAS.md)：核心用户画像。
- [USER_JOURNEY.md](00_product/USER_JOURNEY.md)：构建式、审阅式与企业战略研究旅程。
- [FEATURE_ROADMAP.md](00_product/FEATURE_ROADMAP.md)：当前、下一阶段与企业级路线图。
- [BUSINESS_RULES.md](00_product/BUSINESS_RULES.md)：工作流、审核、数据与报告业务规则。

### 01_research

- [RESEARCH_PHILOSOPHY.md](01_research/RESEARCH_PHILOSOPHY.md)
- [DECISION_FRAMEWORK.md](01_research/DECISION_FRAMEWORK.md)
- [EVIDENCE_STANDARD.md](01_research/EVIDENCE_STANDARD.md)
- [REPORT_STANDARD.md](01_research/REPORT_STANDARD.md)
- [PROMPTS.md](01_research/PROMPTS.md)

### 02_engineering

- [ARCHITECTURE.md](02_engineering/ARCHITECTURE.md)
- [AGENT_WORKFLOW.md](02_engineering/AGENT_WORKFLOW.md)
- [DATABASE.md](02_engineering/DATABASE.md)
- [API.md](02_engineering/API.md)
- [MCP.md](02_engineering/MCP.md)
- [RAG.md](02_engineering/RAG.md)
- [SECURITY.md](02_engineering/SECURITY.md)
- [DEPLOYMENT.md](02_engineering/DEPLOYMENT.md)

### 03_project

- [DECISIONS.md](03_project/DECISIONS.md)
- [TODO.md](03_project/TODO.md)
- [RESEARCH_FLOW_MIGRATION.md](03_project/RESEARCH_FLOW_MIGRATION.md)：完整研究流程的迁移矩阵、阶段状态和实施顺序。
- [STREAMLIT_PARITY_AUDIT.md](03_project/STREAMLIT_PARITY_AUDIT.md)：原 Streamlit 功能与共享 Web 的逐项一致性审计。
- [HANDOFF.md](03_project/HANDOFF.md)
- [CHANGELOG.md](03_project/CHANGELOG.md)
- [RELEASES.md](03_project/RELEASES.md)
- [RETROSPECTIVE.md](03_project/RETROSPECTIVE.md)

### 04_ai

- [AI_MEMORY.md](04_ai/AI_MEMORY.md)

## 维护规则

1. 功能、数据模型、接口或部署方式发生变化时，同一提交中更新对应文档。
2. 关键架构取舍写入 `03_project/DECISIONS.md`，不要只留在聊天记录中。
3. 文档不得包含 API Key、数据库密码、内部文件内容或客户机密。
4. 对尚未完成的能力必须标注“规划”，不得用完成时态描述。
5. 研究规则的变化需要同时检查 `01_research/`、提示词、结构化模型与测试。
6. 功能迁移、新功能和缺陷修复不得只维护 Vercel 或 CloudBase 版本；发布记录必须列出
   两个部署目标的构建与验收结果，区域差异必须是配置或适配器，不得复制业务流程。
