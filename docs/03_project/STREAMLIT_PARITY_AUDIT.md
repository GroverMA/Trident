# Streamlit 功能一致性审计

## 审计基准

- 功能基准：原 GitHub `industry-analyst-os` Streamlit 版本。
- 目标承载：共享 FastAPI + Next.js，部署到 Vercel 海外版和 CloudBase 大陆版。
- 一致性含义：保留研究步骤、人工 Gate、可编辑字段、审核动作、回退规则、产物和导出；
  可以改进界面布局，但不得删除或简化业务能力。
- 状态日期：2026-08-18。

## 核心流程审计

| 原 Streamlit 功能 | 原版行为 | 当前共享 Web 状态 | 必须迁移动作 |
|---|---|---|---|
| 项目创建与研究方式 | 通用/企业，构建式/审阅式，共享项目 | 基础字段已有 | 补齐所有原版入口说明和恢复导航 |
| Prompt Analysis | AI 先解释原始 Prompt | 已纠正并迁移 | 保持 AI 先于人工范围确认 |
| Gate 0 可编辑范围 | 编辑核心市场、产品、客户、地域、时间、产业链、纳入/排除、相邻市场、规模与竞争口径、歧义和回答 | 已重做 | 部署后做真实模型和持久化验收 |
| Research Brief | 必答问题、信息缺口、假设、置信度、方法追踪 | 已迁移 | 补充完整 Methodology 展示 |
| Research Plan | 任务、问题、检索式、来源偏好、证据标准、反证与 Gate | 已迁移但展示仍简化 | 加入检索式、假设、交付物、依赖和反证展示/编辑 |
| Evidence Collection | 按任务搜索、抓取、抽取、冲突与缺口 | 第一批已迁移 | 增加单任务重跑、自定义查询、来源详情和进度 Job |
| Gate 1 Evidence Review | 推荐、全选、逐条接受/拒绝、备注、覆盖缺口处置 | 第一批基础迁移 | 补齐批量选择、推荐逻辑、覆盖建议与缺口确认 |
| Industry Analysis | 行业定义、赛道/产业链、市场规模、竞争、驱动因素与 Findings | 服务存在，Web/API 未完整迁移 | 下一批迁移生成、Finding 审核和人工确认 |
| Gate 2 Content Review | 审核分析与趋势，不通过时局部重跑 | 未迁移 | 迁移 Finding/Trend 审核、依赖失效与回退 |
| Future Intelligence | 驱动/制约、趋势、情景、领先指标、触发与反证 | 服务存在，Web/API 未迁移 | 迁移生成、审阅和情景展示 |
| General Report | 组合专业报告并追溯证据 | 审阅式服务存在，Web 未完整迁移 | 构建式与审阅式共用报告 API/版本 |
| Enterprise Sensing | 文件/自诊断、多批次、敏感级别、接受/拒绝/删除 | 服务和旧 UI 存在，Web 未迁移 | 完整迁移上传、解析、审核和失效规则 |
| Company Scorecard | 动态维度、公司/市场平均/战略目标三线评分 | 服务存在，Web 未迁移 | 迁移指标解释、审核和雷达图 |
| Action Plan | 短期/长期，负责人、开始时间、KPI、依赖、风险、停止条件 | 服务存在，Web 未迁移 | 迁移逐项审核和确认 Gate |
| Enterprise Report | 行业报告 + Scorecard + Action Plan | 服务存在，Web 未迁移 | 迁移组合、审阅和导出 |
| Report Review First | 先生成初稿，再按模块追溯和修订 | 后端流水线存在，Web 入口简化 | 迁移初稿、问答、建议、局部版本 Patch |
| Rewind/Invalidation | 返回上一 Gate，只清除依赖产物 | 领域 helper 存在，Web 未迁移 | 暴露 API、影响预览和确认交互 |
| Word/PDF/Web 导出 | 同一内容和样式，中文字体与引用 | 服务存在，Web 未迁移 | 增加下载端点、视觉回归和双区域验收 |
| 历史项目与恢复 | 保存节点、继续、存档/终止/删除 | 列表和保存基础存在 | 补齐存档、终止、恢复位置和审计 |
| 长任务状态 | 原版页面内进度，失败可重试 | 尚未形成持久化 Job | 迁移为排队/运行/等待人工/失败/恢复状态机 |

## Gate 0 强制顺序

```text
用户原始 Prompt
  → AI Prompt Analysis
  → 生成 Research Brief 与 Market Definition 草稿
  → 用户逐项查看、修改、补充问题与回答
  → 用户确认 Gate 0
  → 写入 market_scope_confirmed_at
  → 生成 Research Plan
```

禁止恢复为“用户先确认范围，再由 AI 分析”的简化顺序。未确认的 AI 草稿必须可保存和
再次编辑；只有人工确认 Gate 0 后，下游 Research Plan 才可运行。

## 发布要求

每恢复一项原版功能，必须同时完成：Application/FastAPI、Next.js、持久化、自动化测试、
Knowledge Base、Vercel 部署和 CloudBase 部署。只有本地通过不算迁移完成。
