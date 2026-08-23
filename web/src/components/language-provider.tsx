"use client";

import { useEffect, useState } from "react";

type Language = "CN" | "EN";

const STORAGE_KEY = "trident_ui_language";

const translations: Record<string, string> = {
  "功能导航": "Navigation",
  "关闭导航": "Close navigation",
  "关闭": "Close",
  "场景决定工作流；知识、信号与行动反馈跨场景持续积累。": "Scenarios define the workflow; knowledge, signals and action feedback accumulate across scenarios.",
  "场景选择": "Scenarios",
  "行业研究 / PE / VC / 企业增长": "Industry Research / PE / VC / Enterprise Growth",
  "项目管理": "Projects",
  "跨场景保存、切换与继续": "Save, switch and continue across scenarios",
  "企业知识库": "Enterprise Knowledge",
  "画像、经营、决策与反馈": "Profiles, operations, decisions and feedback",
  "持续感知": "Continuous Sensing",
  "新闻、政策与经营变化": "News, policy and operating changes",
  "决策与行动质量": "Decision & Action Quality",
  "跨项目反馈与调整 Dashboard": "Cross-project feedback and adjustment dashboard",
  "运营监测": "Operations",
  "Token、耗时与完成情况": "Tokens, latency and completion",
  "研究方法库": "Research Methods",
  "Skill、证据与方法资产": "Skills, evidence and method assets",
  "统一资产层": "UNIFIED ASSET LAYER",
  "一个企业，一套长期记忆": "One enterprise, one long-term memory",
  "不同场景产生的画像、证据、判断、行动和反馈都进入同一企业知识库，并保留来源与版本。": "Profiles, evidence, judgments, actions and feedback from every scenario enter one enterprise knowledge base with provenance and versions.",
  "同一研究内核 · 多场景决策工作流": "One research core · Multi-scenario decision workflows",
  "方法说明": "Method",
  "研究项目": "Research Projects",
  "选择决策场景，": "Choose a decision scenario,",
  "进入完整工作流。": "enter the complete workflow.",
  "AI 咨询不是独立模块，而是每个场景的首个诊断节点。选择场景后，AI 会围绕目标主动提问，并根据资料完整度调整研究路径。": "AI consulting is the first diagnostic node inside every scenario. After you choose a scenario, AI asks adaptive questions around your goal and adjusts the research route to the available evidence.",
  "研究基座": "Research Core",
  "场景包": "Scenario Pack",
  "通用行业研究": "General Industry Research",
  "完整行业定义、规模、竞争、驱动、趋势与报告流程。": "A complete workflow for industry definition, sizing, competition, drivers, trends and reporting.",
  "定义问题 → 研究路径 → 完整报告": "Define question → Research route → Full report",
  "企业增长决策": "Enterprise Growth Decisions",
  "把企业诊断与行业证据映射为增长选择、能力差距和行动计划。": "Map enterprise diagnosis and industry evidence to growth choices, capability gaps and action plans.",
  "主动诊断 → 机会研究 → 战略 → 行动": "Adaptive diagnosis → Opportunity research → Strategy → Action",
  "PE 投资分析": "PE Investment Analysis",
  "成熟企业经营质量、交易边界、价值创造、下行情景与退出研究。": "Operating quality, transaction boundaries, value creation, downside cases and exit research for mature companies.",
  "投资风格 → 标的诊断 → DD → IC Memo": "Investment style → Target diagnosis → DD → IC Memo",
  "VC 投资分析": "VC Investment Analysis",
  "机会发现、团队、技术、市场时点、里程碑和后续融资研究。": "Opportunity discovery, team, technology, market timing, milestones and follow-on financing research.",
  "决策风格 → 初筛 → DD → 投后跟踪": "Decision style → Screening → DD → Portfolio monitoring",
  "进入场景": "Enter scenario",
  "场景服务连接较慢，当前显示稳定入口；进入场景时会再次验证。": "The scenario service is responding slowly. Stable entry points remain available and will be checked again when you enter.",
  "重新连接": "Reconnect",
  "一个共同内核": "One shared core",
  "所有场景共享行业定义、市场规模、竞争格局、驱动因素、证据审阅与报告标准；区别在于访谈对象、决策问题和最终行动输出。": "All scenarios share industry definition, market sizing, competition, drivers, evidence review and reporting standards; they differ in interview subjects, decision questions and action outputs.",
  "项目管理与场景切换": "Project Management & Scenario Switching",
  "所有场景的工作独立保存，并在同一项目空间恢复、查找和继续。切换场景不会覆盖原项目。": "Work from every scenario is saved independently and can be resumed, found and continued in one project space. Switching scenarios never overwrites an existing project.",
  "尚未选择项目": "No project selected",
  "先在项目管理中选择一个工作项目": "Choose an active project in Project Management",
  "切换当前联动项目": "Switch linked project",
  "选择项目": "Select project",
  "知识库": "Knowledge Base",
  "质量 Dashboard": "Quality Dashboard",
  "研究工作台": "Research Workspace",
  "全部项目": "All projects",
  "进行中": "Active",
  "已完成": "Completed",
  "搜索项目、行业或地区": "Search projects, industries or regions",
  "新建场景项目": "New scenario project",
  "当前联动项目": "Linked project",
  "设为联动项目": "Link project",
  "继续工作 →": "Continue →",
  "没有符合条件的项目": "No matching projects",
  "进入场景选择，建立第一个可持续恢复的决策项目。": "Open Scenarios to create your first resumable decision project.",
  "研究范围": "Research Scope",
  "研究规划": "Research Planning",
  "网页研究": "Web Research",
  "证据审核": "Evidence Review",
  "行业分析": "Industry Analysis",
  "未来判断": "Future Intelligence",
  "报告": "Report",
  "持续感知与决策信号": "Continuous Sensing & Decision Signals",
  "自动采集新闻、政策、公司公告和经营变化；先判断与企业、项目和关键假设的关系，再决定是否触发研究或行动调整。": "Collect news, policy, company announcements and operating changes; assess their relevance to entities, projects and assumptions before triggering research or action changes.",
  "今日新增信号": "New signals today",
  "已关联项目": "Linked projects",
  "高影响待复核": "High-impact reviews",
  "去重与分类完成": "Deduplicated & classified",
  "新闻与变化信号": "News & Change Signals",
  "配置关注项目": "Configure watched projects",
  "全部": "All",
  "政策": "Policy",
  "竞争": "Competition",
  "客户": "Customers",
  "技术": "Technology",
  "经营 KPI": "Operating KPIs",
  "行业监管与准入规则出现更新": "Industry regulation and market-access rules updated",
  "政策与监管来源": "Policy and regulatory sources",
  "今日 09:40": "Today 09:40",
  "需要复核市场边界与进入条件": "Market boundaries and entry conditions require review",
  "高影响": "High impact",
  "重点竞争者发布新产品与渠道合作": "Key competitor announces a new product and channel partnership",
  "公司公告 / 行业新闻": "Company announcements / Industry news",
  "昨日 18:20": "Yesterday 18:20",
  "可能改变机会优先级与竞争判断": "May change opportunity priority and competitive assessment",
  "中影响": "Medium impact",
  "下游客户采购周期和需求侧指标变化": "Downstream buying cycles and demand indicators changed",
  "经营数据 / 客户反馈": "Operating data / Customer feedback",
  "8月19日": "Aug 19",
  "关联收入假设与 Action Plan": "Linked to revenue assumptions and Action Plan",
  "待评估": "Pending assessment",
  "从信号到决策动作": "From Signal to Decision Action",
  "抓取与去重": "Collect & deduplicate",
  "新闻、政策、公告与内部数据": "News, policy, announcements and internal data",
  "实体与项目关联": "Link entities and projects",
  "匹配企业、行业、假设和 Action Plan": "Match companies, industries, assumptions and Action Plans",
  "影响评估": "Impact assessment",
  "判断是否改变范围、Scorecard 或优先级": "Assess whether scope, Scorecard or priorities change",
  "人工复核后更新": "Update after human review",
  "创建新版本，不覆盖已批准判断": "Create a new version without overwriting approved judgments",
  "回到关联项目处理影响": "Return to linked project",
  "场景之间共享经过授权和版本化的企业资产，但每个项目仍保留独立证据、判断和流程。": "Scenarios share authorized, versioned enterprise assets while each project retains its own evidence, judgments and workflow.",
  "当前企业 / 标的": "Current company / target",
  "选择企业或投资标的": "Select a company or investment target",
  "先选择一个联动项目，系统会定位对应企业资产。": "Select a linked project to locate the corresponding enterprise assets.",
  "切换关联项目": "Switch linked project",
  "企业画像": "Enterprise Profile",
  "组织、产品、客户、渠道、资源与管理层决策风格。": "Organization, products, customers, channels, resources and management decision style.",
  "经营情况": "Operating Performance",
  "收入、利润、订单、交付和关键经营指标的时间化快照。": "Time-based snapshots of revenue, profit, orders, delivery and key operating indicators.",
  "历史决策": "Decision History",
  "目标、依据、被拒方案、责任人与当时的假设边界。": "Objectives, rationale, rejected options, owners and assumption boundaries.",
  "结果与反馈": "Results & Feedback",
  "Action Plan 进度、实际效果、偏差原因和调整记录。": "Action Plan progress, actual outcomes, variance causes and adjustment records.",
  "企业时间线": "Enterprise Timeline",
  "选择联动项目后显示企业时间线。": "Select a linked project to view the enterprise timeline.",
  "决策与行动质量 Dashboard": "Decision & Action Quality Dashboard",
  "跨项目监测决策、计划设计和执行质量；具体反馈与动态调整仍发生在 PE、VC、企业增长各自的工作流内。": "Monitor decision, plan and execution quality across projects; detailed feedback and adaptive changes remain inside each PE, VC and growth workflow.",
  "决策质量": "Decision Quality",
  "假设验证率、预测偏差与证据—结果一致性": "Hypothesis validation, forecast variance and evidence–outcome consistency",
  "行动质量": "Action Quality",
  "按期完成率、KPI 达成与计划有效性": "On-time completion, KPI achievement and plan effectiveness",
  "执行质量": "Execution Quality",
  "阻塞、责任人反馈、资源到位与完成证据": "Blockers, owner feedback, resource readiness and completion evidence",
  "学习质量": "Learning Quality",
  "反馈完整度、调整时延与重复错误率": "Feedback completeness, adjustment latency and repeated-error rate",
  "选择项目查看决策—行动—结果链路": "Select a project to view the decision–action–outcome chain",
  "反馈入口位于场景项目的 Action Plan 或投后里程碑节点；Dashboard 只聚合并诊断，不静默改写已批准版本。": "Feedback is submitted at Action Plan or portfolio milestone nodes; the dashboard aggregates and diagnoses without silently rewriting approved versions.",
  "进入场景工作流": "Open scenario workflow",
  "选择你的研究方式": "Choose Your Research Path",
  "同一套研究能力，两种不同起点。请先选择路径，再进入对应首页。": "The same research capability with two different starting points. Choose a path before entering its workspace.",
  "同一套专业研究标准，两种不同的工作路径。你可以随时切换，已有研究内容不会丢失。": "One professional research standard, two working paths. You can switch at any time without losing existing work.",
  "构建式研究": "Build-first Research",
  "从问题开始，分步骤与 AI 共同完成研究": "Start from a question and complete the research with AI step by step",
  "从研究目标、市场范围和核心问题出发，逐步完成证据收集、分析验证、结论形成与行动建议。": "Begin with objectives, market scope and core questions, then build evidence, validate analysis, form conclusions and develop action recommendations.",
  "适合：适合希望参与研究过程，并在关键节点确认研究方向的用户。": "Best for: users who want to participate in the process and confirm direction at key checkpoints.",
  "定义问题 → 锁定边界 → 收集证据 → 分析验证 → 形成报告": "Define question → Lock scope → Gather evidence → Validate analysis → Build report",
  "从问题开始": "Start from a question",
  "从问题与范围开始，经过 AI 分析、Gate 0、网页研究、证据审阅、行业分析、趋势与报告。": "Start from a question and scope, then move through AI analysis, Gate 0, web research, evidence review, industry analysis, trends and reporting.",
  "审阅式研究": "Review-first Research",
  "从完整初稿开始审阅，检查和确认您关心的节点": "Start with a complete draft and review the points that matter to you",
  "确认研究范围后，由 AI 先完成报告初稿；你可以从结论出发，检查分析逻辑、引用来源、关键假设和决策依据。": "After the scope is confirmed, AI prepares a full draft. Start from the conclusions and inspect the logic, sources, assumptions and decision rationale.",
  "适合：适合希望快速了解全貌，再针对重点内容深入审阅的用户。": "Best for: users who want the full picture quickly and then review priority topics in depth.",
  "查看结论 → 检查逻辑 → 追溯证据 → 调整判断 → 确认报告": "Review conclusions → Inspect logic → Trace evidence → Adjust judgments → Confirm report",
  "生成报告初稿": "Generate report draft",
  "两种方式使用相同的研究方法、证据标准与报告结构，区别仅在研究过程的呈现顺序。进入后可随时切换，不会重置研究内容。": "Both paths use the same research methods, evidence standards and report structure; only the sequence differs. You can switch later without resetting the research.",
  "从已有报告与资料开始，先生成初稿，再由你审阅并补充研究。": "Start from an existing report and materials, generate a draft, then review and supplement the research.",
  "进入构建式研究": "Enter build-first research",
  "进入审阅式研究": "Enter review-first research",
  "项目内容会在当前浏览器中保存，并通过同一研究服务同步。": "Project content is saved in the current browser and synchronized through the shared research service.",
  "目标校准": "Goal alignment",
  "场景工作流": "Scenario workflow",
  "AI 咨询分析": "AI Consulting Analysis",
  "AI将根据目标主动诊断并形成后续研究任务。": "AI will diagnose the objective and form the next research tasks.",
  "当前进度": "Current progress",
  "诊断画像": "Diagnostic profile",
  "先告诉我，这次最重要的决策是什么？": "What is the most important decision this time?",
  "AI 会根据你的选择改变后续问题，而不是要求你填写一套固定问卷。": "AI adapts subsequent questions to your choices instead of forcing a fixed questionnaire.",
  "增长目标类型": "Growth objective type",
  "第二增长曲线": "Second growth curve",
  "生存型增长": "Survival growth",
  "寻找新市场 / 新产品": "Find new markets / products",
  "收入、利润与现金流优先": "Prioritize revenue, profit and cash flow",
  "企业名称": "Company name",
  "标的公司": "Target company",
  "用于保存项目、画像和后续长期记忆": "Used to save the project, profile and long-term memory",
  "所属行业": "Industry",
  "例如：工业机器人、体外诊断、企业软件": "e.g. industrial robots, IVD, enterprise software",
  "具体目标": "Specific objective",
  "让 AI 开始诊断访谈": "Start AI diagnostic interview",
  "正在建立项目…": "Creating project…",
  "本阶段不会立即输出方案": "This stage does not immediately output a solution",
  "AI 会先形成三项底稿": "AI first creates three working drafts",
  "决策目标契约": "Decision objective contract",
  "明确目标、约束和成功标准": "Clarify objectives, constraints and success criteria",
  "主动问题路径": "Adaptive question path",
  "根据每个回答选择下一问题": "Choose the next question from each answer",
  "资料可得性判断": "Evidence availability assessment",
  "有数据用数据，没有数据允许口述": "Use data when available; allow oral input when it is not",
  "开始语音": "Start voice input",
  "停止并转换为文字": "Stop and convert to text",
  "发送给 AI 并继续": "Send to AI and continue",
  "AI 正在分析回答…": "AI is analyzing the answer…",
  "有资料就上传，没有也可以继续": "Upload materials if available, or continue without them",
  "资料用于校准判断，不是进入下一步的门槛。纸质材料可以先拍照或扫描。": "Materials calibrate the assessment but are not a gate. Paper documents can be photographed or scanned.",
  "选择文件": "Choose files",
  "什么资料都没有？": "No materials at all?",
  "继续回答问题即可。系统会把老板或管理层的口述标记为“待验证判断”，后续再逐步补数。": "Continue answering. Management statements will be marked as judgments to verify and supplemented later.",
  "第一轮企业诊断画像已经形成": "The first diagnostic profile is ready",
  "请先审核画像。确认后，这些内容会作为 Prompt Analysis 和 Gate 0 的场景输入，但待验证判断不会被当作市场事实。": "Review the profile first. Once confirmed, it becomes scenario input for Prompt Analysis and Gate 0; unverified judgments are not treated as market facts.",
  "企业基础画像": "Enterprise foundation profile",
  "经营信息与数字化基础": "Operations and digital foundation",
  "决策风格": "Decision style",
  "管理层如何形成判断": "How management forms judgments",
  "下一研究任务": "Next research task",
  "从诊断进入专业研究流": "From diagnosis to professional research",
  "确认画像并选择研究通路": "Confirm profile and select research route",
  "正在选择研究通路…": "Selecting research route…",
  "在项目管理中查看": "View in Project Management",
  "按推荐通路进入研究内核": "Enter Research Core via recommended route",
  "场景研究上下文": "Scenario research context",
  "诊断访谈已作为研究约束进入共用行业研究底座；场景资料、判断与输出仍按项目独立保存。": "The diagnostic interview now constrains the shared industry research core, while scenario evidence, judgments and outputs remain isolated by project.",
  "已确认诊断画像": "Confirmed diagnostic profile",
  "推荐研究通路": "Recommended research route",
  "数据边界": "Data boundary",
  "经营企业": "Operating company",
  "成熟企业标的": "Mature-company target",
  "创业企业标的": "Venture target",
  "当前项目": "Current project",
  "仅引用本项目及已授权的长期记忆资产": "Uses only this project and authorized long-term memory assets"
};

const attributeNames = ["placeholder", "aria-label", "title"] as const;
const originalText = new WeakMap<Node, string>();
const originalAttributes = new WeakMap<Element, Map<string, string>>();

function translateDynamic(value: string): string {
  return value
    .replace(/主动访谈\s+(\d+)\/(\d+|-)/g, "Adaptive interview $1/$2")
    .replace(/动态问题\s+(\d+)/g, "Adaptive question $1")
    .replace(/当前显示\s+(.+?)\s+的关联资产。后续会按时间串联访谈、研究、决策、行动和结果反馈。/g, "Showing linked assets for $1. Interviews, research, decisions, actions and outcomes will be connected over time.")
    .replace(/(.+?)\s+正在引用该实体的画像、经营事实、历史决策与行动结果。/g, "$1 is using this entity's profile, operating facts, decision history and action outcomes.")
    .replace(/(.+?)\s+·\s+质量诊断/g, "$1 · Quality diagnosis")
    .replace(/AI 对本轮回答的判断/g, "AI assessment of this answer")
    .replace(/仍需澄清：/g, "Needs clarification: ")
    .replace(/你的回答/g, "Your answer")
    .replace(/语音已转换为文字，可以修改后发送给 AI。/g, "Voice converted to text. Edit it before sending to AI.");
}

function shouldSkip(node: Node): boolean {
  const parent = node.parentElement;
  return !parent || Boolean(parent.closest("script,style,.reportContent,.evidenceOriginal,.userAnswer,.uploadedFiles,[data-no-ui-translate]"));
}

function applyEnglish(root: ParentNode = document) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node: Node | null;
  while ((node = walker.nextNode())) {
    if (shouldSkip(node)) continue;
    const raw = node.textContent || "";
    const key = raw.trim();
    if (!key) continue;
    if (!originalText.has(node)) originalText.set(node, raw);
    const translated = translations[key] || translateDynamic(key);
    if (translated !== key) node.textContent = raw.replace(key, translated);
  }
  document.querySelectorAll("[placeholder],[aria-label],[title]").forEach((element) => {
    if (element.closest(".reportContent,[data-no-ui-translate]")) return;
    let saved = originalAttributes.get(element);
    if (!saved) { saved = new Map(); originalAttributes.set(element, saved); }
    attributeNames.forEach((name) => {
      const raw = element.getAttribute(name);
      if (!raw) return;
      if (!saved?.has(name)) saved?.set(name, raw);
      element.setAttribute(name, translations[raw] || translateDynamic(raw));
    });
  });
}

function restoreChinese(root: ParentNode = document) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node: Node | null;
  while ((node = walker.nextNode())) {
    const original = originalText.get(node);
    if (original !== undefined) node.textContent = original;
  }
  document.querySelectorAll("[placeholder],[aria-label],[title]").forEach((element) => {
    const saved = originalAttributes.get(element);
    saved?.forEach((value, name) => element.setAttribute(name, value));
  });
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("CN");

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "EN") window.requestAnimationFrame(() => setLanguage("EN"));
  }, []);

  useEffect(() => {
    document.documentElement.lang = language === "CN" ? "zh-CN" : "en";
    document.documentElement.dataset.uiLanguage = language;
    window.localStorage.setItem(STORAGE_KEY, language);
    if (language === "EN") applyEnglish(); else restoreChinese();
    const observer = new MutationObserver((records) => {
      if (language !== "EN") return;
      records.forEach((record) => record.addedNodes.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE && !shouldSkip(node)) {
          const raw = node.textContent || ""; const key = raw.trim();
          if (key) { if (!originalText.has(node)) originalText.set(node, raw); const translated = translations[key] || translateDynamic(key); if (translated !== key) node.textContent = raw.replace(key, translated); }
        } else if (node instanceof Element) applyEnglish(node);
      }));
    });
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [language]);

  return <><div className="languageSwitcher" role="group" aria-label="界面语言 / Interface language"><button type="button" className={language === "CN" ? "active" : ""} onClick={() => setLanguage("CN")}>CN</button><span>/</span><button type="button" className={language === "EN" ? "active" : ""} onClick={() => setLanguage("EN")}>EN</button></div>{children}</>;
}
