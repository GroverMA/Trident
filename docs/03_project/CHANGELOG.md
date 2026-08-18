# 变更日志

本项目采用面向能力的语义化版本记录。正式发布前的历史原型不强行补造精确版本号。

## Unreleased

### Added

- 产品、研究、工程、项目治理与 AI 记忆知识库。

### Changed

- 无。

### Improved

- 无。

### Fixed

- 无。

### Removed

- 无。

### Known Issues

- 完整异步研究 Job 和持久化恢复仍在规划中。
- CloudBase Demo 的持久化数据库方案尚需最终确认。
- CloudBase 容器已运行，但默认公网域名当前 HTTP/HTTPS 请求超时；需修复公网访问、
  服务端口或 HTTP 网关关联后再进行端到端验收。

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
