"use client";

import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import type { ProjectSummary, ScenarioPackContract } from "@/lib/types";

type Scenario = "general" | "pe" | "vc" | "growth_strategy";
type Stage = "scenarios" | "goal" | "interview" | "profile";

type ScenarioCardView = { id: Scenario; index: string; title: string; english: string; description: string; flow: string; tag: string };

const SCENARIO_ORDER: Scenario[] = ["general", "growth_strategy", "pe", "vc"];
const STABLE_SCENARIO_CARDS: ScenarioCardView[] = [
  { id: "general", index: "01", title: "通用行业研究", english: "GENERAL", description: "完整行业定义、规模、竞争、驱动、趋势与报告流程。", flow: "定义问题 → 研究路径 → 完整报告", tag: "研究基座" },
  { id: "growth_strategy", index: "02", title: "企业增长决策", english: "GROWTH STRATEGY", description: "把企业诊断与行业证据映射为增长选择、能力差距和行动计划。", flow: "主动诊断 → 机会研究 → 战略 → 行动", tag: "场景包" },
  { id: "pe", index: "03", title: "PE 投资分析", english: "PE", description: "成熟企业经营质量、交易边界、价值创造、下行情景与退出研究。", flow: "投资风格 → 标的诊断 → DD → IC Memo", tag: "场景包" },
  { id: "vc", index: "04", title: "VC 投资分析", english: "VC", description: "机会发现、团队、技术、市场时点、里程碑和后续融资研究。", flow: "决策风格 → 初筛 → DD → 投后跟踪", tag: "场景包" },
];

export function ConsultingWorkspace({ initialScenario }: { initialScenario?: Exclude<Scenario, "general"> } = {}) {
  const [stage, setStage] = useState<Stage>(initialScenario ? "goal" : "scenarios");
  const [scenario, setScenario] = useState<Scenario>(initialScenario || "growth_strategy");
  const [scenarioContracts, setScenarioContracts] = useState<ScenarioPackContract[]>([]);
  const [catalogError, setCatalogError] = useState("");
  const [growthType, setGrowthType] = useState("第二增长曲线");
  const [objective, setObjective] = useState("");
  const [targetCompany, setTargetCompany] = useState("");
  const [industry, setIndustry] = useState("");
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [requestError, setRequestError] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState("");
  const [answers, setAnswers] = useState<string[]>([]);
  const [files, setFiles] = useState<string[]>([]);
  const [listening, setListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<{ stop: () => void } | null>(null);
  const answerRef = useRef("");
  const voiceBaseRef = useRef("");
  const voiceFinalRef = useRef("");
  const voiceInterimRef = useRef("");
  const voiceSubmittingRef = useRef(false);
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    fetch("/api/capabilities", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const payload = await response.json() as { scenario_contracts?: ScenarioPackContract[]; detail?: string };
        if (!response.ok) throw new Error(payload.detail || "场景目录暂时无法加载");
        const unique = new Map((payload.scenario_contracts || []).filter((item) => !item.manifest.deprecated).map((item) => [item.manifest.scenario_id, item]));
        setScenarioContracts(SCENARIO_ORDER.map((id) => unique.get(id)).filter(Boolean) as ScenarioPackContract[]);
        setCatalogError("");
      })
      .catch(() => setCatalogError("场景服务连接较慢，当前显示稳定入口；进入场景时会再次验证。"))
      .finally(() => window.clearTimeout(timer));
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [catalogAttempt]);
  const activeContract = scenarioContracts.find((item) => item.manifest.scenario_id === scenario);
  const scenarioCards = useMemo<ScenarioCardView[]>(() => scenarioContracts.length ? scenarioContracts.map((item, index) => ({
    id: item.manifest.scenario_id as Scenario,
    index: String(index + 1).padStart(2, "0"),
    title: item.descriptor.display_name,
    english: item.manifest.scenario_id.replaceAll("_", " "),
    description: item.descriptor.description,
    flow: String(item.ui_schema.card_flow || "场景工作流"),
    tag: item.manifest.scenario_id === "general" ? "研究基座" : "场景包",
  })) : STABLE_SCENARIO_CARDS, [scenarioContracts]);
  const uploadItems = (activeContract?.ui_schema.upload_guides as string[] | undefined) || [];
  const question = project?.interview_session_artifact?.turns.find((turn) => !turn.answer)?.question || "";
  const topicTotal = (project?.interview_session_artifact?.covered_topics.length || 0) + (project?.interview_session_artifact?.remaining_topics.length || 0);
  const progress = topicTotal ? Math.round(((project?.interview_session_artifact?.covered_topics.length || 0) / topicTotal) * 100) : 0;
  const profile = project?.entity_profile_artifact;

  function chooseScenario(next: Scenario) {
    if (next === "general") return;
    setScenario(next); setStage("goal"); setProject(null); setAnswers([]); setAnswer(""); answerRef.current = ""; setFiles([]); setRequestError("");
  }

  async function submitGoal(event: FormEvent) {
    event.preventDefault();
    if (!objective.trim() || !targetCompany.trim() || !industry.trim()) return;
    setBusy(true); setRequestError("");
    try {
      const createdResponse = await fetch("/api/projects", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
        project_name: `${targetCompany}-${activeContract?.descriptor.display_name || "决策项目"}`,
        industry, region: "中国", research_objective: objective, time_horizon: "未来3年", output_language: "简体中文",
        target_company: targetCompany, company_strategy_enabled: true,
        company_strategy_objective:
          scenario === "growth_strategy"
            ? `${growthType}：${objective}`
            : `${scenario === "pe" ? "PE投资判断" : "VC投资判断"}：${objective}`,
        decision_context: objective, research_path: "research_build_first", research_mode: "general_research",
        workspace_mode: "analyst_workspace", scenario_pack: scenario, scenario_pack_version: activeContract?.manifest.version || "1.0.0",
      }) });
      const created = await createdResponse.json() as ProjectSummary & { detail?: string };
      if (!createdResponse.ok) throw new Error(created.detail || "项目创建失败");
      const startResponse = await fetch(`/api/projects/${created.project_id}/interview/start`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ restart: false }) });
      const started = await startResponse.json() as ProjectSummary & { detail?: string };
      if (!startResponse.ok) throw new Error(started.detail || "访谈启动失败");
      setProject(started); setStage("interview");
    } catch (reason) { setRequestError(reason instanceof Error ? reason.message : "诊断服务暂时不可用"); }
    finally { setBusy(false); }
  }
  async function submitAnswer(event: FormEvent) {
    event.preventDefault();
    const submittedAnswer = (answerRef.current || answer).trim();
    if (!submittedAnswer) return;
    voiceSubmittingRef.current = true;
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    if (!project) return;
    const next = [...answers, submittedAnswer]; setAnswers(next); setAnswer(""); answerRef.current = "";
    voiceBaseRef.current = ""; voiceFinalRef.current = ""; voiceInterimRef.current = "";
    setListening(false); setVoiceStatus("");
    setBusy(true); setRequestError("");
    try {
      const response = await fetch(`/api/projects/${project.project_id}/interview/answer`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ answer: submittedAnswer }) });
      const updated = await response.json() as ProjectSummary & { detail?: string };
      if (!response.ok) throw new Error(updated.detail || "回答保存失败");
      setProject(updated);
      if (updated.entity_profile_artifact) setStage("profile");
    } catch (reason) { setAnswers(answers); setAnswer(submittedAnswer); answerRef.current = submittedAnswer; setRequestError(reason instanceof Error ? reason.message : "回答保存失败"); }
    finally { setBusy(false); }
  }
  async function confirmProfile() {
    if (!project || !profile) return;
    setBusy(true); setRequestError("");
    try {
      const response = await fetch(`/api/projects/${project.project_id}/interview/profile`, {
        method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({
          operating_portrait: profile.operating_portrait,
          decision_style: profile.decision_style,
          research_next_step: profile.research_next_step,
          confirm: true,
        }),
      });
      const updated = await response.json() as ProjectSummary & { detail?: string };
      if (!response.ok) throw new Error(updated.detail || "画像确认失败");
      const routeResponse = await fetch(`/api/projects/${updated.project_id}/research-route`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          available_materials: files,
          has_existing_report: files.some((name) => /\.(pdf|docx?|pptx?)$/i.test(name)),
        }),
      });
      const routed = await routeResponse.json() as ProjectSummary & { detail?: string };
      if (!routeResponse.ok) throw new Error(routed.detail || "研究通路选择失败");
      setProject(routed);
    } catch (reason) { setRequestError(reason instanceof Error ? reason.message : "画像确认失败"); }
    finally { setBusy(false); }
  }
  function addFiles(event: ChangeEvent<HTMLInputElement>) { setFiles((current) => [...current, ...Array.from(event.target.files || []).map((file) => file.name)]); }
  function startVoice() {
    type SpeechEvent = { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> };
    type SpeechRecognizer = { lang: string; interimResults: boolean; continuous: boolean; maxAlternatives: number; onstart: () => void; onresult: (event: SpeechEvent) => void; onerror: (event: { error: string }) => void; onend: () => void; start: () => void; stop: () => void };
    const speechWindow = window as typeof window & { SpeechRecognition?: new () => SpeechRecognizer; webkitSpeechRecognition?: new () => SpeechRecognizer };
    const SpeechRecognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    if (!window.isSecureContext) { setVoiceStatus("语音需要安全连接（HTTPS）。请打开线上地址，或使用手机键盘的系统听写。"); return; }
    if (!SpeechRecognition) { setVoiceStatus("当前浏览器不支持网页语音识别。请点击回答框，使用手机键盘上的系统听写；文字会直接进入回答框并可发送给 AI。"); return; }
    if (listening) { recognitionRef.current?.stop(); return; }
    const recognition = new SpeechRecognition();
    const isMobileWebKit = /iPhone|iPad|iPod/i.test(navigator.userAgent)
      || (/Macintosh/i.test(navigator.userAgent) && navigator.maxTouchPoints > 1);
    recognition.lang = "zh-CN"; recognition.interimResults = true; recognition.continuous = !isMobileWebKit; recognition.maxAlternatives = 1;
    voiceBaseRef.current = answerRef.current.trim();
    voiceFinalRef.current = "";
    voiceInterimRef.current = "";
    voiceSubmittingRef.current = false;
    recognition.onstart = () => { setListening(true); setVoiceStatus("正在听，请自然说话；识别结果会转换成可编辑文字。"); };
    recognition.onresult = (event) => {
      let newFinalText = "";
      let interim = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const transcript = event.results[index][0].transcript;
        if (event.results[index].isFinal) newFinalText += transcript; else interim += transcript;
      }
      if (newFinalText.trim()) {
        voiceFinalRef.current = [voiceFinalRef.current, newFinalText.trim()].filter(Boolean).join(" ");
      }
      voiceInterimRef.current = interim.trim();
      const converted = [voiceBaseRef.current, voiceFinalRef.current, voiceInterimRef.current]
        .filter(Boolean)
        .join(" ");
      answerRef.current = converted;
      setAnswer(converted);
      setVoiceStatus(interim.trim() ? `正在识别：${interim.trim()}` : "语音已转换为文字，可以修改后发送给 AI。");
    };
    recognition.onerror = (event) => {
      const messages: Record<string, string> = { "not-allowed": "没有获得麦克风权限。请在手机的浏览器设置中允许麦克风后刷新页面。", "service-not-allowed": "当前浏览器禁止语音识别服务，请改用系统听写或 Safari/Chrome。", "audio-capture": "没有检测到可用麦克风。", "no-speech": "没有听清内容，请靠近麦克风后重试。", aborted: "语音识别已停止，已经识别的文字仍保留在回答框。", network: "语音识别服务连接失败，可改用系统听写或文字输入。" };
      setVoiceStatus(messages[event.error] || `语音识别暂时中断（${event.error}），已保留现有文字。`);
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
      if (voiceSubmittingRef.current) { voiceSubmittingRef.current = false; return; }
      const converted = answerRef.current.trim() || [voiceBaseRef.current, voiceFinalRef.current, voiceInterimRef.current].filter(Boolean).join(" ").trim();
      answerRef.current = converted;
      setAnswer(converted);
      voiceInterimRef.current = "";
      if (converted) setVoiceStatus("语音已转换为文字，可以修改后发送给 AI。");
    };
    recognitionRef.current = recognition;
    try { recognition.start(); } catch { setListening(false); setVoiceStatus("麦克风启动失败，请稍后重试或使用系统听写。"); }
  }

  return <main className="consultingMain">
      <header className="consultingTopbar"><div><span>TRIDENT AI</span><strong>Decision Intelligence Studio</strong></div><nav><a href="#method">方法说明</a><Link href="/research">研究项目</Link></nav></header>
      {stage === "scenarios" && <section className="scenarioLanding">
        <div className="consultingHero"><span className="eyebrow">SCENARIO SELECTION</span><h1>选择决策场景，<br />进入完整工作流。</h1><p>AI 咨询不是独立模块，而是每个场景的首个诊断节点。选择场景后，AI 会围绕目标主动提问，并根据资料完整度调整研究路径。</p></div>
        <div className="scenarioGridNew">
          {scenarioCards.map((item) => item.id === "general" ? <Link href="/research" className="consultingScenarioCard" key={item.id}><ScenarioCard item={item} /></Link> : <button type="button" className={item.id === "growth_strategy" ? "consultingScenarioCard featured" : "consultingScenarioCard"} key={item.id} onClick={() => chooseScenario(item.id)}><ScenarioCard item={item} /></button>)}
        </div>
        {catalogError && <div className="formError" role="alert">{catalogError} <button type="button" onClick={() => setCatalogAttempt((value) => value + 1)}>重新连接</button></div>}
        <div className="consultingPrinciple" id="method"><strong>一个共同内核</strong><span>所有场景共享行业定义、市场规模、竞争格局、驱动因素、证据审阅与报告标准；区别在于访谈对象、决策问题和最终行动输出。</span></div>
      </section>}

      {stage !== "scenarios" && <section className="diagnosticPage">
        <div className="diagnosticBreadcrumb"><button type="button" onClick={() => setStage("scenarios")}>场景选择</button><span>/</span><strong>{activeContract?.descriptor.display_name || "场景工作流"}</strong></div>
        <div className="diagnosticHeader"><div><span className="eyebrow">ACTIVE DIAGNOSTIC INTERVIEW</span><h1>{activeContract?.descriptor.display_name || "AI 咨询分析"}</h1><p>{String(activeContract?.interview_policy.goal || "AI将根据目标主动诊断并形成后续研究任务。")}</p></div><div className="diagnosticStage"><span>当前进度</span><strong>{stage === "goal" ? "目标校准" : stage === "interview" ? `主动访谈 ${answers.length + 1}/${topicTotal || "-"}` : "诊断画像"}</strong></div></div>

        {stage === "goal" && <form className="goalWorkspace" onSubmit={submitGoal}>
          <div className="goalMain"><div className="goalStep"><span>01</span><div><strong>先告诉我，这次最重要的决策是什么？</strong><small>AI 会根据你的选择改变后续问题，而不是要求你填写一套固定问卷。</small></div></div>
            {scenario === "growth_strategy" && <div className="choiceBlock"><label>增长目标类型</label><div className="choicePills">{["第二增长曲线", "生存型增长"].map((item) => <button key={item} type="button" className={growthType === item ? "selected" : ""} onClick={() => setGrowthType(item)}>{item}<small>{item === "第二增长曲线" ? "寻找新市场 / 新产品" : "收入、利润与现金流优先"}</small></button>)}</div></div>}
            <label className="consultingField"><span>{scenario === "growth_strategy" ? "企业名称" : "标的公司"}</span><input value={targetCompany} onChange={(event) => setTargetCompany(event.target.value)} required placeholder="用于保存项目、画像和后续长期记忆" /></label>
            <label className="consultingField"><span>所属行业</span><input value={industry} onChange={(event) => setIndustry(event.target.value)} required placeholder="例如：工业机器人、体外诊断、企业软件" /></label>
            <label className="consultingField"><span>具体目标</span><textarea value={objective} onChange={(event) => setObjective(event.target.value)} required rows={5} placeholder={scenario === "growth_strategy" ? "例如：未来三年销售额翻倍，同时把单一大客户收入占比降到20%以下。" : scenario === "vc" ? "例如：判断某机器人项目是否值得进入正式DD，重点验证技术壁垒与商业化速度。" : "例如：判断该标的能否通过渠道整合和运营改善，在五年内实现目标回报。"} /></label>
            {requestError && <div className="formError" role="alert">{requestError}</div>}
            <button className="primaryButton consultingPrimary" type="submit" disabled={busy}>{busy ? "正在建立项目…" : "让 AI 开始诊断访谈"}</button>
          </div>
          <aside className="goalAside"><span>本阶段不会立即输出方案</span><h2>AI 会先形成三项底稿</h2><ol><li><strong>决策目标契约</strong><small>明确目标、约束和成功标准</small></li><li><strong>主动问题路径</strong><small>根据每个回答选择下一问题</small></li><li><strong>资料可得性判断</strong><small>有数据用数据，没有数据允许口述</small></li></ol></aside>
        </form>}

        {stage === "interview" && <div className="interviewWorkspace">
          <section className="interviewChat"><div className="interviewProgress"><span style={{width:`${progress}%`}} /></div><div className="interviewThread">{(project?.interview_session_artifact?.turns || []).filter((turn) => turn.answer).map((turn) => <div className="answerPair" key={turn.turn_id}><div className="aiQuestion"><span>AI</span><p>{turn.question}</p></div><div className="userAnswer"><p>{turn.answer}</p><span>你的回答</span></div>{turn.analysis && <div className="answerAnalysis"><strong>AI 对本轮回答的判断</strong><p>{turn.analysis.summary}</p>{turn.analysis.ambiguities.length > 0 && <small>仍需澄清：{turn.analysis.ambiguities.join("；")}</small>}</div>}</div>)}<div className="aiQuestion current"><span>AI</span><div><small>动态问题 {answers.length + 1}</small><p>{question}</p><em>AI 会先分析本轮答案；信息不明确时会追问，充分后才进入下一主题。</em></div></div></div>
            <form className="interviewComposer" onSubmit={submitAnswer}><textarea value={answer} onChange={(event) => { answerRef.current = event.target.value; setAnswer(event.target.value); }} rows={4} inputMode="text" enterKeyHint="done" placeholder="用你习惯的方式回答，不需要整理成正式材料…" />{voiceStatus && <p className="voiceStatus" role="status">{voiceStatus}</p>}{project?.interview_session_artifact?.provider_warning && <p className="voiceStatus" role="status">{project.interview_session_artifact.provider_warning}</p>}{requestError && <p className="formError" role="alert">{requestError}</p>}<div><button type="button" aria-pressed={listening} aria-label={listening ? "停止语音识别并保留文字" : "开始语音识别"} className={listening ? "voiceButton listening" : "voiceButton"} onClick={startVoice}>{listening ? "停止并保留文字" : "开始语音"}</button><button type="submit" className="primaryButton" disabled={busy}>{busy ? "AI 正在分析回答…" : "发送给 AI 并继续"}</button></div></form>
          </section>
          <aside className="evidenceDrawer"><span className="eyebrow">OPTIONAL MATERIALS</span><h2>有资料就上传，没有也可以继续</h2><p>资料用于校准判断，不是进入下一步的门槛。纸质材料可以先拍照或扫描。</p><div className="uploadGuide">{uploadItems.map((item) => <span key={item}>{item}</span>)}</div><input ref={fileRef} type="file" multiple hidden onChange={addFiles} /><button type="button" className="secondaryButton uploadButton" onClick={() => fileRef.current?.click()}>选择文件</button>{files.length > 0 && <ul className="uploadedFiles">{files.map((file) => <li key={file}>{file}</li>)}</ul>}<div className="oralOption"><strong>什么资料都没有？</strong><p>继续回答问题即可。系统会把老板或管理层的口述标记为“待验证判断”，后续再逐步补数。</p></div></aside>
        </div>}

        {stage === "profile" && profile && <section className="profileWorkspace" id="profile"><div className="profileLead"><span className="eyebrow">DIAGNOSTIC OUTPUT</span><h1>第一轮企业诊断画像已经形成</h1><p>请先审核画像。确认后，这些内容会作为 Prompt Analysis 和 Gate 0 的场景输入，但待验证判断不会被当作市场事实。</p></div><div className="profileGrid"><article><span>01 · 企业基础画像</span><h2>经营信息与数字化基础</h2><p>{profile.operating_portrait}</p></article><article><span>02 · 决策风格</span><h2>管理层如何形成判断</h2><p>{profile.decision_style}</p></article><article><span>03 · 下一研究任务</span><h2>从诊断进入专业研究流</h2><p>{profile.research_next_step}</p></article></div><div className="profileEvidenceBands"><div><strong>已提取事实</strong><span>{profile.known_facts.length ? profile.known_facts.join("；") : "尚无经过结构化提取的事实"}</span></div><div><strong>管理层口述与判断</strong><span>{profile.management_judgments.length ? profile.management_judgments.join("；") : "暂无"}</span></div><div><strong>后续验证缺口</strong><span>{profile.data_gaps.length ? profile.data_gaps.join("；") : "暂无显著缺口"}</span></div></div>{project?.research_route_artifact && <div className="workflowPreview"><strong>推荐研究通路 · {project.research_route_artifact.mode_label}</strong><span>{project.research_route_artifact.rationale.join(" ")}</span></div>}{requestError && <p className="formError" role="alert">{requestError}</p>}<div className="profileActions"><Link className="secondaryButton" href="/projects">在项目管理中查看</Link>{profile.human_confirmed && project?.research_route_artifact ? <Link className="primaryButton" href={`/research?project=${project?.project_id || ""}`}>按推荐通路进入研究内核</Link> : <button className="primaryButton" type="button" disabled={busy} onClick={confirmProfile}>{busy ? "正在选择研究通路…" : "确认画像并选择研究通路"}</button>}</div>{scenario === "growth_strategy" ? <EnterpriseFlow growthType={growthType} /> : scenario === "vc" ? <VCFlow /> : <div className="workflowPreview"><strong>后续完整研究流</strong><span>{String(activeContract?.ui_schema.card_flow || "行业研究 → 场景分析 → 人工审核 → 决策输出")}</span></div>}</section>}
      </section>}
    </main>;
}

function EnterpriseFlow({ growthType }: { growthType: string }) {
  return <section className="enterpriseFlow" id="memory"><div className="enterpriseFlowHead"><div><span className="eyebrow">ENTERPRISE DECISION WORKFLOW</span><h2>{growthType}决策流</h2></div><p>行业研究只围绕增长决策所需的问题展开，不生成通用行业报告。</p></div><div className="enterpriseFlowGrid">
    <article className="active"><span>01</span><h3>增长目标与企业画像</h3><p>访谈与资料合并输入，识别经营边界、资源、数据缺口和管理层决策风格。</p><small>当前阶段</small></article>
    <article><span>02</span><h3>双增长曲线机会研究</h3><p>第一曲线评估核心产品×场景与买家采购；第二曲线评估核心能力×高增长下游与进入路线。</p><small>预留下游应用与战略分析 Skill 接口</small></article>
    <article><span>03</span><h3>Opportunity Scorecard</h3><p>以机会为评分单元，同时比较企业现状、市场平均和实现目标所需能力，5条长名单收敛至不超过3条。</p><small>产品场景适配 · 买家采用 · 单位经济性 · 资源与风险</small></article>
    <article><span>04</span><h3>1–2个 Action Plan</h3><p>只对最终优先机会形成负责人、资源、客户验证、领先/结果指标及停止或转向条件。</p><small>客户接触 → 测试 → 报价/试单 → 成交 → 动态调整</small></article>
  </div><div className="enterpriseOutputs"><div><strong>Company Scorecard</strong><span>机会吸引力 / 产品场景适配 / 买家采用 / 单位经济性 / 进入路径 / 资源缺口 / 可逆性</span></div><div><strong>Action Plan</strong><span>最终1–2条机会 / 责任人 / 资源 / 客户验证 / KPI / 停止或转向条件</span></div></div></section>;
}

function VCFlow() {
  return <section className="enterpriseFlow"><div className="enterpriseFlowHead"><div><span className="eyebrow">VC DECISION WORKFLOW</span><h2>从投资假设到可验证里程碑</h2></div><p>行业研究用于独立验证市场和技术叙事；最终输出必须适配基金决策风格与标的阶段。</p></div><div className="enterpriseFlowGrid">
    <article className="active"><span>01</span><h3>投资风格与标的画像</h3><p>识别基金偏好、淘汰标准、团队与技术信号，以及当前最关键的不确定性。</p><small>当前阶段</small></article>
    <article><span>02</span><h3>独立研究与DD</h3><p>构建市场时点、竞争、客户、技术与商业模式证据，避免直接接受BP中的融资叙事。</p><small>完整DD资料可审阅式进入，缺口仍补充构建研究</small></article>
    <article><span>03</span><h3>Investment Scorecard</h3><p>比较当前证据、基金门槛和下一里程碑门槛，形成推进、观察或暂不推进判断。</p><small>市场时点 · 团队 · 技术壁垒 · PMF证据 · Runway · 下行风险</small></article>
    <article><span>04</span><h3>里程碑与投后反馈</h3><p>把未证实假设转成验证任务、融资与经营里程碑，并根据创始人和客户反馈更新跟投判断。</p><small>支持 / 跟投 / 观察 / 退出条件</small></article>
  </div><div className="enterpriseOutputs"><div><strong>Investment Scorecard</strong><span>当前证据 / 基金门槛 / 下一里程碑门槛 / 关键风险</span></div><div><strong>Milestone Plan</strong><span>假设负责人 / 所需证据 / Runway影响 / 跟投触发 / 停止或退出条件</span></div></div></section>;
}

function ScenarioCard({ item }: { item: ScenarioCardView }) {
  return <><div className="scenarioCardTop"><span>{item.index}</span><em>{item.tag}</em></div><small>{item.english}</small><h2>{item.title}</h2><p>{item.description}</p><div>{item.flow}</div><strong>进入场景 <span>→</span></strong></>;
}
