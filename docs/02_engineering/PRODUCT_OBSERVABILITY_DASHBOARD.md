# 产品运行监测 Dashboard 设计

## 1. 目标与用户

该后台服务产品经理、研究运营和工程负责人，用于回答：一份报告花了多少 Token 与时间、成本集中在哪个节点、哪里失败或重试、不同模型和研究模式的效率是否变化。

普通研究用户默认看不到后台。经组织管理员授权的客户可获得只读 `analytics_viewer` 权限，只查看其组织数据；内部 `product_ops` 可查看跨项目聚合，平台管理员才可查看错误诊断字段。

## 2. 部署建议

生产方案采用“同仓库、独立应用、共享观测数据库”：

- 用户端继续部署为 `trident-research`。
- 内部后台部署为独立 Vercel Project，例如 `trident-ops`，入口不出现在普通导航。
- 两者使用同一 GitHub `main` 和共享的 PostgreSQL Telemetry Schema。
- 后台通过组织/角色鉴权和行级权限读取数据，不直接访问用户报告正文、Prompt 或网页原文。
- Vercel Preview 只连接测试 Telemetry 数据库；Production 连接正式数据库。
- 腾讯云商业化部署沿用相同事件合同，可写入区域内 PostgreSQL，再由区域内后台查看；默认不跨境同步研究内容。

当前 Demo 尚无完整用户和组织体系，因此第一阶段只建立事件合同和内部开关，不采用“隐藏 URL 即安全”的做法。正式开放前必须接入身份认证、RBAC 和组织隔离。

## 3. 事件数据模型

每个模型、搜索和研究节点写入不可变事件：

```text
research_run
  run_id, project_id, organization_id, research_path, model_provider,
  started_at, completed_at, status, total_tokens, total_duration_ms

step_run
  step_run_id, run_id, step_name, attempt, status,
  started_at, completed_at, duration_ms,
  prompt_tokens, completion_tokens, reasoning_tokens, cached_tokens,
  model_calls, search_calls, crawl_calls, source_count,
  error_category, retryable

model_call
  call_id, step_run_id, provider, model, started_at, duration_ms,
  prompt_tokens, completion_tokens, reasoning_tokens, cached_tokens,
  status, error_category
```

禁止记录 API Key、完整 Prompt、模型完整回答、用户文件或网页正文。研究内容与运行指标使用不同表和不同访问权限。

## 4. 指标定义

### 首屏指标

- 完成报告数：筛选窗口内 `decision_report=completed` 的唯一 Run 数。
- 报告完成率：完成 Run ÷ 已启动 Run。
- 单报告 Token：完成 Run 的 `total_tokens` 中位数，同时展示 P75/P95。
- 单报告耗时：从首次研究节点开始到报告完成的墙钟时间中位数。
- 失败/重试率：发生失败或 `attempt > 1` 的 Step Run ÷ 全部 Step Run。
- 本期估算模型成本：按模型版本和 Token 计价表计算，需标注价格版本。

### 诊断视图

- 按研究节点的 Token、耗时和失败率堆叠/趋势。
- 按模型、研究路径、区域、组织、行业和版本筛选。
- 单报告瀑布：Prompt Analysis → Planning → Evidence → Analysis → Future → Report。
- 失败任务表：节点、任务 ID、错误类别、发生时间、是否可重试，不显示敏感正文。
- 搜索质量：搜索次数、抓取成功率、可抽取正文率、来源数和最终接受证据数。

## 5. 页面布局

1. 顶部全局筛选：时间、环境、研究路径、模型、组织、状态。
2. KPI 卡：报告数、完成率、Token 中位数、耗时中位数、重试率、估算成本。
3. 趋势区：每日报告量及 Token/耗时走势。
4. 节点效率区：各步骤 Token 与耗时分布、失败率。
5. 单报告明细：项目、步骤、开始/完成时间、Token、调用次数、状态。
6. 数据健康：最后事件时间、无 Usage 返回比例、未闭合 Run 数、事件写入延迟。

## 6. 数据质量和告警

- `total_tokens` 必须等于各 Step Token 之和；各 Step 必须等于所属 Model Call 之和。
- Provider 未返回 Usage 时记录 `usage_missing=true`，不得估成精确值。
- 已完成报告必须拥有开始时间、完成时间和至少一个模型调用。
- 超过阈值仍为 `in_progress` 的 Run 标记为悬空，不计入成功率分母之外的“完成”。
- 告警首批覆盖：抓取成功率骤降、P95 节点耗时升高、Token/报告异常、认证失败激增。

## 7. 实施顺序

1. 建立不可变 Telemetry Schema 和模型/搜索/步骤事件采集。
2. 接入 PostgreSQL、迁移和事件一致性测试。
3. 建立仅内部可访问的 `/ops` Dashboard 与产品指标 API。
4. 接入身份、组织、RBAC、RLS 和审计日志。
5. 完成客户只读授权流程、数据保留与区域化部署。
