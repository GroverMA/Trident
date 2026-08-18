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
6. 原 Streamlit 版是功能一致性基准；Next.js 可以重构视觉和技术边界，但不得删除原有
   字段、人工审核、回退、版本、企业流程或导出能力。详细差距见
   [Streamlit 功能一致性审计](STREAMLIT_PARITY_AUDIT.md)。

## 当前矩阵

| 阶段 | Application/FastAPI | Next.js | 持久化/测试 | 状态 |
|---|---|---|---|---|
| 项目与研究路径 | 已迁移 | 模式选择前置、项目管理侧栏和创建首页已恢复 | 已覆盖 | 完成，待双端线上验收 |
| Prompt Analysis / Gate 0 / Research Brief | AI 先分析、人工后确认的顺序已迁移 | 原 Prompt、术语理解、完整市场边界、歧义问答和确认动作已恢复 | 已覆盖 | 完成，待双端线上验收 |
| Research Plan | 已迁移 | 已迁移 | 已覆盖 | 完成 |
| 网页检索与 Evidence Matrix | 已迁移；单任务抓取失败保留错误与缺口，不伪造证据 | 已迁移；移除成功后的错误刷新链路 | 已覆盖 | 完成（第二轮修复） |
| Gate 1 证据接受/拒绝 | 已迁移；支持带限制继续和缺口确认 | 已迁移；系统推荐/全选/取消、缺口表、必选确认已恢复 | 已覆盖 | 完成（第二轮修复） |
| 返回上一审核节点 | 领域回退规则与 FastAPI 已迁移 | Web Research/Gate 1 可返回最近 Gate，保留前序并清除失效产物 | 已覆盖 | 完成 |
| 移动项目管理 | 共享数据/API | 手机端可收起抽屉导航 | 浏览器 390×844 验收 | 完成 |
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
  将项目推进至 Industry Analysis；存在覆盖缺口时必须保存用户选择、确认时间及可选专家
  输入，缺口本身不形成无限检索或硬阻断。
- `POST /v1/projects/{project_id}/rewind`：返回最近的人工 Gate；保留该 Gate 之前的产物，
  清除依赖已变更前序信息的后续分析、趋势和报告。

## 后续实施顺序

1. Industry Analysis 生成、Finding 审核与确认。
2. Future Intelligence 生成、趋势/情景审核与 Gate 2。
3. General Report 生成、内容版本和 Word/PDF 导出。
4. Enterprise Sensing、Company Scorecard、Action Plan 与 Enterprise Report。
5. 模块级修订、历史版本和恢复。
6. 将同步长任务封装为持久化 Job/Worker，并为四条主路径建立双区域 E2E。

## 当前 Web 流程契约

构建式研究界面的八个共享节点不得改名、删除或合并：Prompt Analysis、Gate 0 · Scope、
Web Research、Gate 1 · Evidence、Industry Analysis、Future Intelligence、Gate 2 · Content、
General Report。项目管理侧栏与研究方式切换属于所有节点共享的应用壳层，不是首页的临时组件。

## 证据研究不中断契约

1. 搜索或抓取的单个来源失败只进入 `search_errors`，不得让已取得的其他证据丢失。
2. 没有正文的来源不能生成 Evidence；系统明确显示信息缺口，不得虚构替代内容。
3. 覆盖不完整不阻断研究：用户可接受分析师处理建议，或补充自己的判断后继续；后续产物
   必须降低相应结论置信度并标注证据边界。
4. Gate 1 仍要求至少一条人工接受的可用证据，并要求用户明确确认来源、原文和适用范围。
5. 返回上一节点后，页面不得重复使用旧分支的审核勾选或失效结论。
