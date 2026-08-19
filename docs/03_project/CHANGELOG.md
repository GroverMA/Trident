# 变更日志

本项目采用面向能力的语义化版本记录。正式发布前的历史原型不强行补造精确版本号。

## Unreleased

### Added

- 产品、研究、工程、项目治理与 AI 记忆知识库。
- CloudBase 单域名公开健康探针 `/healthz` 和就绪探针 `/readyz`。
- 共享 Web 研究流程的 Evidence Collection、Evidence Matrix 和 Gate 1 人工审核。
- 前置的构建式/审阅式研究方式选择页，以及共享项目管理侧栏。
- FastAPI 安全回退接口、Gate 1 证据缺口处理契约和手机端项目导航抽屉。
- 共享 Web 研究流程的 Industry Analysis 五模块生成、Finding 接受/拒绝、审核备注与人工确认 Gate。
- 五个版本化专业研究 Skill、运行时 Registry、模块级 Prompt 绑定和产物版本/哈希审计。
- 共享 Web 研究流程的 Future Intelligence 生成、趋势/情景逐项审核与 Gate 2 准入。
- Gate 2 内容确认与 General Report 生成、失败后保留审核状态的安全重试通路。
- 内部 `/ops` 产品运行 Dashboard、双层访问保护、真实模型 Usage 与步骤耗时埋点。

### Changed

- 确立 Vercel 海外版与腾讯云大陆版的双区域同源原则：共享研究流程、功能、契约、Skill
  和版本，区域差异仅由部署配置与基础设施适配表达。
- 构建式研究工作台恢复为 Streamlit 同源的八节点英文流程；Gate 0 恢复原 Prompt、AI 术语理解、完整市场边界和逐项人工确认。
- Web 字体切换为 Streamlit 同源的 Source Sans 系列优先栈，桌面密度与手机端应用壳层按原版重新校准。
- 当前融资与产品验证阶段以 Vercel 和后续自有域名为主 Demo 通路；CloudBase 保留为中国大陆商业化部署预研，不再阻塞当前 Demo 功能迁移。

### Improved

- 无。

### Fixed

- 容器 CI 现在显式启用单实例 Demo 的 SQLite 模式，与 CloudBase 运行配置保持一致，避免生产环境安全检查拒绝启动。
- 修复研究操作成功后重复刷新路由造成的字符串格式假错误。
- Gate 1 在证据覆盖不完整时可由用户明确选择“带限制继续”，同时保留缺口、处理建议和确认审计记录。
- CloudBase 未随 Vercel 更新的原因已定位为缺少实际发布触发/凭证，而非代码或镜像构建失败。
- 修复 Web 版要求逐项点击趋势/情景才可继续的迁移偏差；恢复 Streamlit 的“默认采用、明确排除”语义，未操作项不再无故阻断流程。
- 网页研究改为逐任务请求与逐任务持久化，避免整批搜索超过浏览器或 Vercel 请求窗口；失败任务可从断点继续。
- 外部搜索或证据抽取失败时写回可重试状态和安全错误摘要，不再把项目永久留在 `in_progress`。
- 统一服务端与浏览器端的上海时区时间格式，消除研究页面的 React hydration 错误。

### Removed

- 无。

### Known Issues

- 完整异步研究 Job 和持久化恢复仍在规划中。
- CloudBase Demo 的持久化数据库方案尚需最终确认。
- Demo 阶段 Telemetry 随项目 JSON 保存；正式 append-only PostgreSQL Schema、组织级 RBAC/RLS 和搜索/抓取指标尚未实施。
- CloudBase 默认域名在中国大陆本地网络可访问，但会隔离部分境外或自动化网络；大陆
  验收必须使用目标区域网络，不能把外部探测超时直接判断为服务不可用。

## 0.3.0 — 2026-08-17

### Added

- FastAPI 服务基线、项目与研究范围相关 API。
- Next.js 正式 Web 工作台基线。
- Scenario、Industry、Algorithm 等可插拔扩展合同。
- CloudBase 中国大陆 Demo 部署配置。
- 显式 SQLite Demo 模式与 PostgreSQL 正式环境边界。

### Changed

- Trident 成为独立升级仓库，不再修改原 Industry Analyst 项目。
- 部署策略调整为同一代码库支持海外与中国大陆配置。

### Fixed

- CloudBase 根目录部署入口。
- CloudBase 容器内 pnpm 运行时依赖缺失。
- Demo 环境缺少 PostgreSQL 连接时无法启动的问题，改为显式 SQLite Demo 配置。

## Prototype — 早期验证阶段

### Validated

- 通用行业研究与企业战略研究的核心流程。
- 构建式研究与审阅式研究两种进入路径。
- 网页搜索、证据审核、行业分析、趋势预测、报告导出。
- 企业资料接入、Company Scorecard 与 Action Plan 的概念验证。

> 早期原型的具体变更以原仓库提交历史为准，本文件不虚构未确认的发布日期和版本号。
