# 场景插件化第一阶段审计（2026-08-21）

## 审计目标

在不改变现有行业研究行为的前提下，确认 Trident 从行业研究产品扩展为 PE、VC、企业增长决策平台时的共享基座、耦合点、迁移边界和回归基线。

## 最终判断

现有行业研究不是四个并列场景中的一个普通页面，而是所有场景共享的 **Research Core**。PE、VC 和企业增长必须调用行业研究的专业节点与证据对象，不得复制、删减或建立另一套低标准研究链路。

当前代码已经具备版本化扩展注册表和稳定行业研究服务，但 Scenario Pack 仍是“提示词约束包”，不是可执行插件。下一阶段需要扩展合同并增加通用 Workflow Runner，而不是改写研究核心。

## 当前已经完成并必须保护的基座

1. 构建式与审阅式两条研究路径。
2. Prompt Analysis、Gate 0、Research Plan、Web Research、Gate 1、Industry Analysis、Future Intelligence、Gate 2、General Report。
3. 行业定义、赛道与产业链、独立市场规模测算、竞争格局、驱动因素及未来情景方法包。
4. Evidence、Finding、Trend、Scenario 和 Report 的结构化产物与人工审核状态。
5. 回退、失效、版本、来源追溯与项目持久化规则。
6. 企业资料、Company Scorecard、Action Plan 和 Enterprise Report 的现有服务能力。
7. FastAPI 统一业务边界、Next.js 客户端和 Vercel/腾讯云同一 `main` 基线原则。

## 当前实现差距

### 场景合同不足

`ScenarioPack` 当前只有：

- `descriptor`
- `research_instructions()`
- `required_inputs()`

它只能向 Prompt Analysis 和 Research Plan 注入场景文本，不能声明完整工作流、访谈、审核、输出、界面和评价标准。

### PE 与 VC 未拆分

当前内置包仍为 `pe_vc@1.0.0`。PE 与 VC 的投资阶段、风险结构、判断逻辑、人工 Gate 和交付物不同，必须迁移为 `pe@1.0.0` 与 `vc@1.0.0`。

### 前端场景硬编码

- TypeScript 把场景类型固定为 `general | sme_growth | pe_vc`。
- 行业研究高级模式直接把 `scenario_pack` 切换为 `sme_growth`。
- AI 咨询原型在组件内保存 PE、VC、Growth 的问题、上传建议、流程文案和条件分支。

这些逻辑应由 API 返回的 `ui_schema`、`interview_policy` 和 `workflow` 驱动。

### AI 咨询仍是原型

当前访谈为固定问题数组，画像由前端关键词判断；文件只保存文件名，语音依赖浏览器 SpeechRecognition。尚未接入后端会话、模型追问、企业证据、Portfolio 或长期记忆。

### 持续感知尚未形成跨场景平台

现有 `enterprise_sensing` 主要处理企业资料生命周期和战略流程准入，不等于新闻/政策/KPI监测、变化检测、影响重估、提醒和决策版本更新的持续感知系统。

## 允许改变与禁止改变

### 允许改变

- 扩展 Scenario Pack 合同。
- 增加通用 Workflow Runner。
- 将场景文案、问题、节点和输出迁入版本化场景包。
- 增加旧场景 ID 迁移适配器。
- 让行业研究节点输出可被其他场景消费的结构化接口。

### 禁止改变

- 不得为 PE、VC、企业增长复制行业研究服务。
- 不得降低专业 Skill、证据和市场规模测算要求。
- 不得删除构建式、审阅式或行业研究高级模式。
- 不得因为插件化改变现有项目的研究节点、人工决定或历史版本。
- 不得引入 Vercel 与腾讯云两套业务代码。

## 回归基线

审计当日验证：

- Python：`183 passed`。
- Web ESLint：通过。
- Next.js 生产构建：通过。
- 已生成的主要路由包括 `/research`、项目工作台、报告页、企业页、健康检查和内部运营页。

以上结果是第二阶段场景合同改造的最低回归线。后续每批变更必须至少重复执行这三项检查，并增加四个场景的契约和端到端测试。

## 第二阶段输入

1. 定义可执行 `ScenarioPackContract`。
2. 增加通用 Workflow Runner 和节点类型。
3. 保持 `general@1.0.0` 行为不变，先作为参考实现接入新合同。
4. 建立 `pe`、`vc`、`growth_strategy` 空壳场景包和契约测试。
5. 为 `sme_growth` 与 `pe_vc` 建立显式迁移映射，暂不删除历史支持。

## 实施进展

- 第二阶段：完整合同、通用Runner、四个目标场景和两个deprecated兼容入口已完成。
- 第三阶段：Next.js场景目录、首轮访谈问题、资料建议和流程摘要已改为从合同读取。
- 能力目录已从模型配置解耦，无模型密钥也能读取场景。
- 当前行业研究基座行为不变。
- 最新回归：Python 187项测试、Web检查、生产构建和本地浏览器验收通过。
- 下一项：后端动态访谈会话、结构化画像、Portfolio/长期记忆，以及合同节点到实际服务的持久化调度。
