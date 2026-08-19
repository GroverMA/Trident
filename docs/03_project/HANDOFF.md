# 项目交接说明

- **最后更新**：2026-08-19
- **当前仓库**：Trident
- **当前分支**：`main`
- **当前里程碑**：Vercel 主 Demo 完整研究流程迁移；CloudBase 商业化部署预研

## 最近完成

- 场景化迁移第一批已完成：`general@1.0.0`、`sme_growth@1.0.0`、`pe_vc@1.0.0` 通过共享 Registry 加载，场景约束进入 Brief 与 Plan，未复制研究 Agent。
- 从原型仓库复制并独立建立 Trident，不再修改原 Industry Analyst。
- 建立 Python + FastAPI + Next.js 的升级基线和可插拔合同。
- 增加 CloudBase 中国大陆 Demo 部署文件，并保留海外部署。
- 增加显式 SQLite Demo 模式，正式环境仍以 PostgreSQL 为目标。
- 修复 CloudBase 根目录、运行时依赖和容器构建问题。
- CloudBase 修复提交 `758adda` 已部署，容器运行状态正常。
- 海外地址 `https://trident-research.vercel.app` 的首页和项目 API 已通过公网检查。
- 腾讯云默认域名已确认，用户侧中国大陆本地网络可以访问；部分境外或自动化网络受
  CloudBase 网页隔离策略影响会出现 TLS 超时，不能据此判断服务故障。
- 已新增公网 `/healthz` 与 `/readyz` 探针，并在本地生产形态验证均返回 HTTP 200。
- 完整流程迁移第一批已完成：构建式路径可从 Research Plan 执行网页检索、持久化
  Evidence Matrix、逐条接受/拒绝证据，并在确认 Gate 1 后进入 Industry Analysis。
- 已按原 Streamlit 版纠正 Prompt Analysis/Gate 0：AI 先解释 Prompt，用户再逐项修改
  市场范围和研究问题，确认后才进入 Research Plan。
- 已建立 `STREAMLIT_PARITY_AUDIT.md`，后续迁移以原版完整功能而非当前简化 Web 为基准。
- 已按 Streamlit 截图恢复前置研究方式选择、共享项目管理侧栏、构建式八节点工作台和完整 Gate 0；本地浏览器桌面/移动验收通过。
- 已恢复 Streamlit Gate 1 的系统推荐/全选/取消、证据缺口处理、必选确认与安全回退；
  覆盖缺口可带限制继续，不再把未覆盖问题变成无限检索或硬阻断。
- 已修复研究操作成功后额外路由刷新导致的 `The string did not match the expected pattern.`
  假失败；项目状态现在由 API 返回值直接更新。
- 手机端项目管理已改为可开启/关闭的抽屉导航，桌面端保持固定项目栏。
- 建立本套产品、研究、工程、项目治理和 AI 记忆文档。
- Industry Analysis 已迁入共享 Application/FastAPI/Next.js：五个模块、Finding 证据追溯、
  接受/拒绝、审核备注和人工确认 Gate 均持久化；确认后开放 Future Intelligence。

## 当前重点

继续迁移 Future Intelligence、Gate 2 和 General Report，随后把长任务迁移为可恢复的异步 Job。

所有迁移和新增功能仍必须保持单一 `main`、共享功能、研究流程、API/数据契约、Skill 与
报告标准。当前融资 Demo 只以 Vercel/自有域名作为上线验收通路；CloudBase 不再阻塞当前
Demo，但其部署适配继续保留，未来进入中国大陆商业化阶段时恢复区域发布验收。

## 待完成

1. 腾讯云控制台完成登录后，将 CloudBase Git 自动部署分支固定为 `main`，或为 GitHub
   Actions 配置 TCB 三项 Secret；发布同一 SHA 后从大陆浏览器确认 `/healthz`、
   `/readyz`、首页与项目 API。
2. 为 Demo SQLite 设置持久化或迁移至 CloudBase PostgreSQL。
3. 验证模型和搜索凭证仅存在于服务端环境变量。
4. 逐条执行通用/企业 × 构建式/审阅式端到端测试。
5. 补齐长任务队列、恢复机制和模块级修订测试。

## 当前阻塞与风险

- CloudBase 默认域名具有区域网络访问限制；大陆端到端验收必须从中国大陆目标网络
  执行，并与海外 Vercel 验收共同记录。
- 当前 GitHub/CloudBase 之间没有可执行的发布凭证或自动部署门禁；容器 CI 通过不会更新
  线上 CloudBase 服务。本轮必须在腾讯云登录后完成一次控制台绑定/发布，之后才能恢复
  真正的双区域同步发布。
- CloudBase 共享 PostgreSQL 可能不提供传统外网连接串，需选择平台数据库 API 或独享数据库。
- SQLite 位于无持久卷容器时，实例重建会导致数据丢失。
- 搜索和模型服务属于外部依赖，额度、网络和凭证失效均会影响研究任务。
- 曾通过界面截图展示过凭证；上线前应轮换相关密钥，不应从历史对话恢复并继续使用。
- 当前公开仓库未发现许可证文件；公开可见不等于自动授予复制、修改或商业使用权。

## 重要上下文

- 双区域同源是最高优先级约束：允许部署和基础设施不同，不允许业务能力不同；任何变更
  都要记录两个区域的构建与验收状态。
- 两种研究方式共享同一项目数据，只改变流程的呈现顺序。
- 企业战略路径必须先获得企业战略意图和经审核的一手信息，再生成 Scorecard 与 Action Plan。
- Scorecard 使用公司、市场平均、战略目标三条评分线；市场平均不能被误写为理想分。
- Action Plan 必须针对市场差距与战略目标差距，并明确做什么、谁负责、何时开始。
- 报告正文不得出现内部 Evidence/Finding 编码、系统提示词、证据缺口模板或特定研究机构品牌。

## 建议接手顺序

1. 阅读[项目上下文](../00_product/PROJECT_CONTEXT.md)。
2. 阅读[系统架构](../02_engineering/ARCHITECTURE.md)与[Agent 工作流](../02_engineering/AGENT_WORKFLOW.md)。
3. 阅读[AI 长期记忆](../04_ai/AI_MEMORY.md)。
4. 检查当前 Git 状态和最近提交。
5. 运行自动化测试，再进行 CloudBase 健康检查和一条最小端到端研究。

## 交接记录模板

```markdown
- 日期：
- 交接人：
- 当前分支与提交：
- 已完成：
- 正在进行：
- 阻塞：
- 下一步：
- 风险与回滚方式：
```
