# 企业增长决策与永久 Agent 导航设计 QA

- source visual truth: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-36f0a87d-8b34-4a85-8ebe-f610506021df.png`
- industry form reference: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-dd978801-1a48-4454-a682-668610cd342d.png`
- implementation screenshots: `qa-enterprise-goal.jpg`, `qa-enterprise-flow.jpg`, `qa-industry-form.jpg`
- desktop viewport: 1440 × 900, density 1
- mobile viewport: 390 × 844, density 1
- state: 企业决策目标校准、四轮访谈完成、行业研究构建式表单

## Full-view comparison evidence

源图定义的是四阶段企业增长决策框架，页面实现将相同结构转译为可操作流程：增长目标与企业画像、市场机会与下游应用、Company Scorecard、Action Plan 与增长复盘。源图的信息密度属于方案图，产品页面改为逐步呈现，避免用户一次阅读完整流程表。深蓝、青绿色、浅灰背景和线性阶段层级与 Trident 视觉语言一致。

## Focused region comparison evidence

- 输入区：第二增长曲线/生存型增长与具体目标被置于首屏，并明确 AI 不会立即输出方案。
- 访谈区：语音与文字共享同一个回答框，识别状态、停止操作和错误提示可见；资料上传是可选项。
- 输出区：企业画像后展示四阶段决策流，并明确通用行业报告不适用于该场景。
- 行业研究：原“研究场景”三卡片与高级模式开关已移除，只保留构建式/审阅式双入口和通用研究表单。
- 导航：Agent 导航在企业决策和行业研究页面持续存在；移动端同时需要项目导航时，两枚按钮并列且可独立展开。

## Required fidelity surfaces

- Fonts and typography: 通过；标题、阶段名、说明和小标签层级清晰，移动端无异常断行。
- Spacing and layout rhythm: 通过；桌面目标页保持主次双栏，流程输出为四列；移动端自动转单列。
- Colors and visual tokens: 通过；沿用 Trident 深蓝、青绿色和浅灰表面色。
- Image quality and asset fidelity: 不适用；源图用于流程结构，页面没有需要复制的图像资产。
- Copy and content: 通过；增长目标、下游应用、Scorecard、Action Plan、动态复盘和 Skill 接口均明确呈现。

## Primary interactions tested

- 永久在线 Agent 导航在 `/enterprise` 与 `/research` 可见
- 企业增长目标选择与目标输入
- 四轮访谈连续提交并生成企业画像
- Company Scorecard 与 Action Plan 流程展示
- 行业研究进入构建式表单后不再显示场景模块
- 390px 手机端 Agent 导航与项目导航并列
- lint 与 production build 通过

## Findings and comparison history

1. P1：初版全局导航在行业研究内部与项目导航的手机按钮重叠。修复为两枚独立按钮并列，复测 390px 页面均可访问。
2. P2：带锚点的导航条目曾被错误标记为当前模块。修复激活规则，仅真实页面路由显示当前状态。

语音识别依赖浏览器与系统麦克风权限，无法在自动化验收中授权真实录音；已验证支持检测、实时/最终文本处理、停止、权限错误、无语音、无麦克风及网络失败反馈。正式产品仍应接入服务器端语音转写作为跨浏览器兜底。

final result: passed

---

# 跨工作台网页联动 QA（2026-08-21）

- implementation URL: `http://127.0.0.1:3000`
- viewport: 1492 × 838 CSS px；density 1
- state: 项目管理选择当前项目 → 企业知识库 → 持续感知 → 行动反馈
- browser-rendered evidence: 项目名称 `高级模式构建式回归测试` 在三个独立工作台保持一致

## Findings and fixes

- P1：独立页面此前只共享视觉导航，没有共享当前项目上下文。已增加持久化联动项目选择器，并在知识库、持续感知、行动反馈和研究工作台间复用。
- P1：页面按钮部分为静态展示。已将项目设为联动项目、跨工作台跳转、持续感知分类筛选、返回关联研究项目和反馈入口接通。

## Validation

- 项目管理选择第二个项目后，企业知识库显示同一项目：通过。
- 跳转持续感知后项目选择保持：通过。
- “政策”筛选将信号列表收敛为 1 条：通过。
- 跳转行动反馈后标题显示同一项目 Action Plan：通过。
- 浏览器 console error/warning：0。
- ESLint、TypeScript、Next.js production build：通过。

Demo 当前仅在浏览器保存非敏感项目 ID；正式多用户版本必须迁移到服务端用户/租户上下文。

final result: passed

---

# 独立平台工作台重构 QA（2026-08-21）

- source visual truth path: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-86dc22f6-d82e-488c-89af-7df6c5e09f6e.png`
- implementation screenshots: `/private/tmp/trident-scenario-only-home-qa.png`、`/private/tmp/trident-sensing-workspace-qa.png`、`/private/tmp/trident-project-management-qa.png`
- combined comparison: `/private/tmp/trident-workspace-separation-comparison.png`
- viewport: 1492 × 838 CSS px；density 1
- state: 场景选择、持续感知、项目管理三个独立页面

## Comparison evidence

源截图暴露的 P1 信息架构问题是企业知识库、持续感知与场景卡纵向堆叠在同一首页，同时项目清单以导航下拉展开。修复后首页首屏及完整页面只包含四个场景和共同内核说明；项目管理、企业知识库、持续感知、行动反馈分别使用独立路由。持续感知页面已包含新闻/政策/竞争/客户/KPI 分类、信号列表、影响等级及从信号到决策动作的路由。项目管理页使用 Portfolio 卡片、筛选、搜索、进度与继续入口。

## Required fidelity surfaces

- Fonts and typography: passed；沿用现有中英文层级和字重。
- Spacing and layout rhythm: passed；独立页面首屏均形成单一主要任务，没有长首页模块串联。
- Colors and visual tokens: passed；沿用深蓝、青绿、浅灰与白色表面。
- Image quality and asset fidelity: passed；本轮无需要复制的图像资产，也未使用伪造图形资产。
- Copy and content: passed；页面任务、数据联动边界和人工复核原则均明确。

## Interactions and validation

- 左侧场景选择、项目管理、持续感知路由切换通过
- 场景首页确认不存在知识库和持续感知详细模块
- 项目筛选、搜索控件和继续工作入口可见
- 持续感知新闻分类、影响路由和高影响入口可见
- 浏览器 console error/warning：0
- ESLint、TypeScript、Next.js production build：通过

## Comparison history

- P1：同级模块被堆叠在同一滚动页。已拆分为独立工作台，复测通过。
- P2：项目列表在全局导航中展开造成拥挤。已替换为“项目管理”独立入口和 Portfolio 页面，复测通过。

final result: passed

---

# 场景入口与跨场景平台导航重构 QA（2026-08-21）

- source visual truth path: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-6a4fbfa8-c104-4d02-8651-c29c51eef7e7.png`
- implementation screenshot path: `/private/tmp/trident-scenario-navigation-qa.png`
- mobile screenshots: `/private/tmp/trident-scenario-navigation-mobile-qa.png`、`/private/tmp/trident-scenario-navigation-mobile-open-qa.png`
- combined comparison: `/private/tmp/trident-scenario-navigation-comparison.png`
- viewport: desktop 1492 × 838 CSS px；mobile 390 × 844 CSS px；device density 1
- source pixels: 2984 × 1675，按 2x 参考密度归一为 1492 × 838
- implementation pixels: 1492 × 838
- state: 场景选择首页；进行中的工作展开；企业增长场景目标校准；移动端导航展开

## Full-view comparison evidence

合并对照图确认实现继续沿用参考图的深蓝固定侧栏、白色顶栏、左右分栏 Hero、四张等权场景卡和浅青色共同内核说明。重构只改变信息架构：左栏从业务场景列表改为一个场景入口及跨场景能力，主区场景卡仍保持原视觉层级。标题字级、四列密度、侧栏宽度、色彩和留白与参考设计一致，没有出现横向溢出或核心控件被裁切。

## Focused region comparison evidence

- 左侧导航：已验证只有“场景选择”一个业务入口；进行中的工作可展开并展示最近项目；企业知识库、持续感知、行动反馈与自进化、运营监测、研究方法库为同级平台能力。
- 场景卡：四个场景仍由 `/api/capabilities` 配置驱动；企业增长入口点击后进入目标校准，面包屑显示“场景选择 / 企业增长决策”。
- 移动端：390px 下首屏为单列卡片，功能导航可打开和关闭，全部跨场景能力可见。
- 页面下段：企业知识层、持续感知和行动反馈闭环采用独立锚点，左侧导航可直达。

## Required fidelity surfaces

- Fonts and typography: passed；字体族、标题权重、字距、中文换行和小标签层级与既有设计一致。
- Spacing and layout rhythm: passed；侧栏、Hero、四列卡片与说明条保持参考图比例，移动端转为单列。
- Colors and visual tokens: passed；复用 Trident 深蓝、青绿、浅灰和白色表面色，没有引入新的视觉体系。
- Image quality and asset fidelity: passed；参考页没有需要复制的核心图像资产，本次也未使用占位图、手绘 SVG 或 CSS 图形替代资产。
- Copy and content: passed；AI 咨询被明确为场景首节点，跨场景保存、知识沉淀、持续感知和 Action Plan 动态版本均有直接说明。

## Primary interactions tested

- 展开/收起“进行中的工作”，读取并显示最近五个项目
- 从场景首页进入企业增长目标校准
- 返回场景选择页
- 390px 手机端打开全局功能导航
- 浏览器 console error/warning：0
- Web ESLint、TypeScript 与 Next.js production build：通过

## Findings and comparison history

- 第一轮未发现可操作的 P0/P1/P2 视觉差异。参考图中左侧逐一列出的场景被有意合并为“场景选择”，这是本次产品要求，不属于视觉漂移。
- 浏览器指针停留在“进行中的工作”时出现浅色 hover 状态，属于既有交互反馈；离开后恢复深色，不影响状态辨识。

## Follow-up polish

- P3：后续接入真实跨场景项目后，可在最近工作条目增加场景名称与更新时间；当前行业研究项目数据模型尚未完整保存四类场景显示名。

final result: passed
