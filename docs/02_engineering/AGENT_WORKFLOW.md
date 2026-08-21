# Agent Workflow

## 1. Purpose

Trident 的 Agent 工作流不是“一次 Prompt 生成报告”，而是以研究状态机组织问题定义、证据收集、判断形成、人工确认、战略评分与行动计划。模型负责推理和表达，代码负责边界、状态、校验、追溯与责任节点。

## 2. Logical Agents

当前代码可由多个服务协作完成，不要求每个逻辑 Agent 都独立运行成进程。

| 逻辑角色 | 主要职责 | 关键产物 |
|---|---|---|
| Intake / Profile Agent | 主动提问、理解用户目标、形成行业/企业/标的画像 | Structured Brief、Profile |
| Research Planner | 将研究目标拆成任务、问题、证据要求和验收条件 | Research Plan |
| Search Agent | 形成搜索策略、搜索网页并抓取正文 | Source Candidates |
| Evidence Agent | 提取事实、数据、观点，记录来源和适用范围 | Evidence Matrix |
| Analysis Agent | 依照 SOP 形成行业定义、产业链、规模与竞争判断 | Industry Analysis |
| Future Intelligence Agent | 驱动因素、领先信号、情景、反证与预测 | Trends、Scenarios |
| Simulation Agent | 模拟投资委员会、竞争者、客户或管理层判断 | Counterarguments、Decision Tests |
| Scorecard Agent | 计算公司、市场基准与战略目标的动态维度差距 | Company Scorecard |
| Action Planning Agent | 将差距转化为短期/长期行动 | Action Plan |
| Report Agent | 组织专业叙事、引用、Word/PDF 输出 | Report Versions |
| Review Agent | 解释审阅问题，只修改选定模块并保留其余内容 | Revision Patch、Review Conversation |

## 3. Responsibilities Boundary

- Agent 不自行扩大研究范围。
- 所有事实必须能追溯到证据或明确标为推断。
- 所有战略建议必须关联企业目标和差距。
- Agent 不删除人工修改，除非用户明确要求覆盖。
- Agent 不在正式报告中暴露内部 Evidence ID、Finding ID 或系统错误。
- 缺少某一来源不等于停止研究；应使用交叉验证、区间估算、代理变量或降低内部置信度。

## 4. Inputs

- 原始研究 Prompt。
- 行业、地区、时间范围、目标公司。
- 企业战略意图与经营痛点。
- 企业自我诊断与管理者决策风格。
- 已审核的一手文件、观察和内部数据。
- SOP、Industry Pack、Scenario Pack。
- 网页、数据库、招股书、政策和公司披露。

## 5. Outputs

- Market Definition 与 Clarification Responses。
- Research Brief、Research Plan、Task Runs。
- Evidence Matrix 与质量/相关性评分。
- Industry Analysis、Future Intelligence、Scenarios。
- Company Scorecard、Benchmark Gap、Action Plan。
- General Report 或 Enterprise Report。
- 审阅记录、版本差异、风险提示与责任边界。

## 6. Tool Selection

工具由编排层根据任务类型调用：

- `search_web`：发现候选网页和来源。
- `crawl_page`：抓取具体页面正文。
- Model API：结构化抽取、分析、反证、写作与审阅对话。
- File Extractors：解析 DOCX、XLSX、PPTX、PDF、TXT、MD、CSV。
- Python Algorithms：市场规模计算、趋势拟合、情景计算和评分。
- Report Exporters：网页、Word、PDF。
- Database/Object Storage：状态、证据、版本和文件保存。

## 7. State Management

每个项目至少记录：

- 当前节点与完成比例。
- 原始输入和已确认范围。
- 每项任务的状态、重试次数和产物版本。
- Evidence 是否采用、拒绝或删除。
- 人工确认与修改内容。
- 报告版本、模块版本和父版本。
- Scorecard 输入、计算依据和置信度。
- Action Plan 与执行反馈。

构建式与审阅式研究只改变节点呈现顺序，不复制项目数据。

## 8. Error Handling

1. 外部调用设置超时、有限重试和退避。
2. JSON 解析前进行容错清洗，解析后通过 Pydantic 校验。
3. 枚举、可选字段与未知引用必须归一化，不能直接让页面崩溃。
4. 已完成阶段持久化后，下游失败不得触发重复搜索。
5. 下游失败展示可理解的恢复操作，不暴露完整堆栈给最终用户。
6. 允许从失败节点重跑，也允许返回更早节点修改并明确下游失效范围。

## 9. Human-in-the-loop

关键人工节点包括：

- Gate 0：市场口径与研究范围确认。
- Evidence Review：来源真实性、适用性和采用范围确认。
- Content Review：报告生成前对判断和趋势进行确认。
- Content Revision：审阅者选择模块、提出问题、接受建议并生成局部新版本。
- Enterprise Sensing Review：企业资料接受、拒绝或删除。

## 10. Logging and Audit

记录工具调用的时间、类型、耗时、状态、来源 URL、模型与 Token 使用量，但不得记录明文密钥。每个判断需能关联到产物版本和责任节点。

## 11. Monitoring

至少监控：任务成功率、阶段耗时、模型失败率、搜索成功率、结构校验失败率、报告生成成功率、单位报告成本、人工退回率和模块重生成率。

## 12. Extension Model

新增行业或场景时优先添加：

1. Scenario Pack：用户流程、专属输入、决策输出。
2. Industry Pack：分类体系、关键指标、术语和来源偏好。
3. Skill：可执行研究方法和结构化输出协议。
4. Algorithm Strategy：量化评分、预测或仿真。
5. Artifact Evaluator：自动质量检查与回归测试。
