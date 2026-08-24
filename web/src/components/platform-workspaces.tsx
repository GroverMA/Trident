"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { ProjectSummary, ScenarioPackContract } from "@/lib/types";

const ACTIVE_PROJECT_KEY = "trident_active_project_id";
const stageLabels: Record<string, string> = { research_brief: "研究范围", research_planning: "研究规划", evidence_collection: "网页研究", evidence_qa: "证据审核", industry_analysis: "行业分析", future_intelligence: "未来判断", decision_report: "报告" };
function progress(project: ProjectSummary) { const states = Object.values(project.workflow_status || {}); return states.length ? Math.round(states.filter((item) => item === "completed").length / states.length * 100) : 0; }

function useLinkedProjects() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeId, setActiveIdState] = useState("");
  useEffect(() => { fetch("/api/projects", { cache: "no-store" }).then((r) => r.ok ? r.json() : []).then((rows: ProjectSummary[]) => { setProjects(rows); const requested = new URLSearchParams(window.location.search).get("project"); const saved = window.localStorage.getItem(ACTIVE_PROJECT_KEY); const preferred = requested || saved; setActiveIdState(preferred && rows.some((row) => row.project_id === preferred) ? preferred : (rows[0]?.project_id || "")); }).catch(() => setProjects([])); }, []);
  function setActiveId(id: string) { setActiveIdState(id); window.localStorage.setItem(ACTIVE_PROJECT_KEY, id); }
  function replaceProject(project: ProjectSummary) { setProjects((rows) => rows.map((row) => row.project_id === project.project_id ? project : row)); }
  return { projects, activeId, activeProject: projects.find((project) => project.project_id === activeId), setActiveId, replaceProject };
}

function LinkedContextBar({ projects, activeId, onChange }: { projects: ProjectSummary[]; activeId: string; onChange: (id: string) => void }) {
  const active = projects.find((project) => project.project_id === activeId);
  return <div className="linkedContext"><div><span>当前联动项目</span><strong>{active?.project_name || "尚未选择项目"}</strong><small>{active ? `${active.industry} · ${active.region} · ${stageLabels[active.current_step] || active.current_step}` : "先在项目管理中选择一个工作项目"}</small></div><select value={activeId} onChange={(event) => onChange(event.target.value)} aria-label="切换当前联动项目"><option value="">选择项目</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select><nav><Link href="/knowledge">知识库</Link><Link href="/sensing">持续感知</Link><Link href="/feedback">质量 Dashboard</Link>{active && <Link href={`/projects/${active.project_id}`}>研究工作台</Link>}</nav></div>;
}

export function WorkspaceHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <><header className="consultingTopbar"><div><span>TRIDENT AI</span><strong>Decision Intelligence Studio</strong></div><nav><Link href="/">场景选择</Link><Link href="/projects">项目管理</Link></nav></header><div className="platformPageHero"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div></>;
}

export function ProjectManagementWorkspace() {
  const { projects, activeId, setActiveId } = useLinkedProjects(); const [query, setQuery] = useState(""); const [filter, setFilter] = useState("all");
  const rows = useMemo(() => projects.filter((p) => `${p.project_name} ${p.industry} ${p.region}`.toLowerCase().includes(query.toLowerCase())).filter((p) => filter === "all" || (filter === "active" ? p.workflow_status.decision_report !== "completed" : p.workflow_status.decision_report === "completed")), [projects, query, filter]);
  return <main><WorkspaceHeader eyebrow="PROJECT PORTFOLIO" title="项目管理与场景切换" description="所有场景的工作独立保存，并在同一项目空间恢复、查找和继续。切换场景不会覆盖原项目。"/><section className="platformPage"><LinkedContextBar projects={projects} activeId={activeId} onChange={setActiveId}/><div className="projectToolbar"><div><button className={filter === "all" ? "selected" : ""} onClick={() => setFilter("all")}>全部项目</button><button className={filter === "active" ? "selected" : ""} onClick={() => setFilter("active")}>进行中</button><button className={filter === "done" ? "selected" : ""} onClick={() => setFilter("done")}>已完成</button></div><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索项目、行业或地区"/><Link className="primaryButton" href="/">新建场景项目</Link></div><div className="projectPortfolioGrid">{rows.map((project) => <article className={project.project_id === activeId ? "activeProject" : ""} key={project.project_id}><div className="projectMeta"><span>{project.scenario_pack || "general"}</span><small>{new Date(project.updated_at).toLocaleDateString("zh-CN")}</small></div><h2>{project.project_name}</h2><p>{project.industry} · {project.region}</p><div className="projectProgress"><span style={{width:`${progress(project)}%`}}/></div><footer><div><strong>{progress(project)}%</strong><small>{stageLabels[project.current_step] || project.current_step}</small></div><div className="projectActions"><button type="button" onClick={() => setActiveId(project.project_id)}>{project.project_id === activeId ? "当前联动项目" : "设为联动项目"}</button><Link href={`/projects/${project.project_id}`}>继续工作 →</Link></div></footer></article>)}{!rows.length && <div className="platformEmpty"><h2>没有符合条件的项目</h2><p>进入场景选择，建立第一个可持续恢复的决策项目。</p></div>}</div></section></main>;
}

const signals = [
  { type: "政策", title: "行业监管与准入规则出现更新", source: "政策与监管来源", time: "今日 09:40", impact: "需要复核市场边界与进入条件", level: "高影响" },
  { type: "竞争", title: "重点竞争者发布新产品与渠道合作", source: "公司公告 / 行业新闻", time: "昨日 18:20", impact: "可能改变机会优先级与竞争判断", level: "中影响" },
  { type: "客户", title: "下游客户采购周期和需求侧指标变化", source: "经营数据 / 客户反馈", time: "8月19日", impact: "关联收入假设与 Action Plan", level: "待评估" },
];

export function SensingWorkspace() {
  const { projects, activeId, activeProject, setActiveId } = useLinkedProjects(); const [signalFilter, setSignalFilter] = useState("全部"); const visibleSignals = signalFilter === "全部" ? signals : signals.filter((signal) => signal.type === signalFilter);
  return <main><WorkspaceHeader eyebrow="CONTINUOUS SENSING" title="持续感知与决策信号" description="自动采集新闻、政策、公司公告和经营变化；先判断与企业、项目和关键假设的关系，再决定是否触发研究或行动调整。"/><section className="platformPage"><LinkedContextBar projects={projects} activeId={activeId} onChange={setActiveId}/><div className="sensingSummary"><article><span>24</span><small>今日新增信号</small></article><article><span>7</span><small>已关联项目</small></article><article><span>3</span><small>高影响待复核</small></article><article><span>86%</span><small>去重与分类完成</small></article></div><div className="sensingLayout"><section className="signalFeed"><div className="sectionTitle"><div><span className="eyebrow">SIGNAL INBOX</span><h2>新闻与变化信号</h2></div><Link href="/projects">配置关注项目</Link></div><div className="signalFilters">{["全部","政策","竞争","客户","技术","经营 KPI"].map((item) => <button key={item} className={signalFilter === item ? "selected" : ""} onClick={() => setSignalFilter(item)}>{item}</button>)}</div>{visibleSignals.map((item) => <article className="signalRow" key={item.title}><span>{item.type}</span><div><h3>{item.title}</h3><p>{item.source} · {item.time}</p><strong>{item.impact}</strong></div><em>{item.level}</em></article>)}</section><aside className="impactPanel"><span className="eyebrow">IMPACT ROUTER</span><h2>从信号到决策动作</h2><ol><li><span>01</span><div><strong>抓取与去重</strong><small>新闻、政策、公告与内部数据</small></div></li><li><span>02</span><div><strong>实体与项目关联</strong><small>匹配企业、行业、假设和 Action Plan</small></div></li><li><span>03</span><div><strong>影响评估</strong><small>判断是否改变范围、Scorecard 或优先级</small></div></li><li><span>04</span><div><strong>人工复核后更新</strong><small>创建新版本，不覆盖已批准判断</small></div></li></ol><Link className="primaryButton linkButton" href={activeProject ? `/projects/${activeProject.project_id}` : "/projects"}>回到关联项目处理影响</Link></aside></div></section></main>;
}

export function KnowledgeWorkspace() {
  const { projects, activeId, activeProject, setActiveId } = useLinkedProjects();
  const timeline = [...(activeProject?.enterprise_timeline_events || [])].reverse();
  const currentVersion = activeProject?.action_plan_artifact?.version || 1;
  return <main><WorkspaceHeader eyebrow="ENTERPRISE KNOWLEDGE BASE" title="企业知识库" description="场景之间共享经过授权和版本化的企业资产，但每个项目仍保留独立证据、判断和流程。"/><section className="platformPage"><LinkedContextBar projects={projects} activeId={activeId} onChange={setActiveId}/><div className="knowledgeEntity"><div><span>当前企业 / 标的</span><h2>{activeProject?.target_company || activeProject?.industry || "选择企业或投资标的"}</h2><p>{activeProject ? `${activeProject.project_name} 正在引用该实体的画像、经营事实、历史决策与行动结果。当前 Action Plan 为 V${currentVersion}，历史版本 ${activeProject.action_plan_history?.length || 0} 份。` : "先选择一个联动项目，系统会定位对应企业资产。"}</p></div><Link href="/projects">切换关联项目</Link></div><div className="platformCapabilityGrid"><article><span>01</span><h3>企业画像</h3><p>组织、产品、客户、渠道、资源与管理层决策风格。</p></article><article><span>02</span><h3>经营情况</h3><p>收入、利润、订单、交付和关键经营指标的时间化快照。</p></article><article><span>03</span><h3>历史决策</h3><p>目标、依据、被拒方案、责任人与当时的假设边界。</p></article><article><span>04</span><h3>结果与反馈</h3><p>Action Plan 进度、实际效果、偏差原因和调整记录。</p></article></div><div className="knowledgeTimeline"><h2>企业时间线</h2>{timeline.length > 0 ? <ul className="timelineList">{timeline.map((event) => <li key={event.event_id}><time>{new Date(event.occurred_at).toLocaleString("zh-CN")}</time><div><strong>{event.title}</strong><small>{event.summary}</small></div></li>)}</ul> : <p>{activeProject ? "尚无已批准的计划调整。访谈、研究和原计划继续保留；只有人工批准的新版本才会写入此时间线。" : "选择联动项目后显示企业时间线。"}</p>}</div></section></main>;
}

const feedbackLabels: Record<string, string> = {
  customer_feedback: "客户反馈", owner_comment: "负责人说明", management_feedback: "管理层反馈",
  founder_feedback: "创始人反馈", milestone_metrics: "里程碑结果", runway: "Runway 变化",
};

export function FeedbackWorkspace() {
  const { projects, activeId, activeProject, setActiveId, replaceProject } = useLinkedProjects();
  const [contracts, setContracts] = useState<ScenarioPackContract[]>([]);
  const [actionId, setActionId] = useState("");
  const [progressPct, setProgressPct] = useState(0);
  const [outcomeMetrics, setOutcomeMetrics] = useState("");
  const [blockers, setBlockers] = useState("");
  const [scenarioFields, setScenarioFields] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [revisionDecisions, setRevisionDecisions] = useState<Record<string, "needs_review" | "accepted" | "rejected">>({});
  const [revisionBusy, setRevisionBusy] = useState(false);
  useEffect(() => { fetch("/api/capabilities", { cache: "no-store" }).then((r): Promise<{ scenario_contracts?: ScenarioPackContract[] }> => r.ok ? r.json() : Promise.resolve({})).then((payload) => setContracts(payload.scenario_contracts || [])).catch(() => setContracts([])); }, []);
  const actions = useMemo(() => (activeProject?.action_plan_artifact?.actions || []).filter((item) => item.review_status === "accepted"), [activeProject]);
  const selectedActionId = actions.some((item) => item.action_id === actionId) ? actionId : (actions[0]?.action_id || "");
  const contract = contracts.find((item) => item.manifest.scenario_id === activeProject?.scenario_pack);
  const policyFields = Array.isArray(contract?.feedback_policy?.feedback_fields) ? contract.feedback_policy.feedback_fields as string[] : [];
  const extraFields = policyFields.filter((field) => !["progress_pct", "outcome_metrics", "blockers", "evidence_refs"].includes(field));
  const entries = useMemo(() => activeProject?.action_feedback_artifact?.entries || [], [activeProject]);
  const latest = useMemo(() => { const rows = new Map<string, typeof entries[number]>(); entries.forEach((entry) => { const current = rows.get(entry.action_id); if (!current || entry.submitted_at > current.submitted_at) rows.set(entry.action_id, entry); }); return rows; }, [entries]);
  const coverage = actions.length ? Math.round(latest.size / actions.length * 100) : 0;
  const averageProgress = latest.size ? Math.round([...latest.values()].reduce((sum, item) => sum + item.progress_pct, 0) / latest.size) : 0;
  const blockerCount = [...latest.values()].filter((item) => item.blockers.trim()).length;
  const revision = activeProject?.plan_revision_artifact;
  const decisionFor = (proposalId: string, current: "needs_review" | "accepted" | "rejected") => revisionDecisions[proposalId] || current;
  const revisionReady = Boolean(revision?.proposals.length) && revision!.proposals.every((item) => decisionFor(item.proposal_id, item.review_status) !== "needs_review");

  async function submitFeedback(event: React.FormEvent) {
    event.preventDefault(); if (!activeProject || !selectedActionId) return;
    setSaving(true); setMessage(""); setError("");
    try {
      const response = await fetch(`/api/projects/${activeProject.project_id}/action-feedback`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ action_id: selectedActionId, progress_pct: progressPct, outcome_metrics: outcomeMetrics, blockers, evidence_refs: [], scenario_fields: scenarioFields }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "反馈保存失败");
      replaceProject(payload); setMessage("反馈已写回项目和企业知识库；原 Action Plan 未被自动覆盖。");
      setOutcomeMetrics(""); setBlockers(""); setScenarioFields({});
    } catch (reason) { setError(reason instanceof Error ? reason.message : "反馈保存失败"); }
    finally { setSaving(false); }
  }

  async function generateRevision() {
    if (!activeProject) return;
    setRevisionBusy(true); setMessage(""); setError("");
    try {
      const response = await fetch(`/api/projects/${activeProject.project_id}/plan-revision`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "偏差诊断生成失败");
      replaceProject(payload); setRevisionDecisions({}); setMessage("偏差诊断已生成。请逐项审核，系统不会自动修改原计划。");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "偏差诊断生成失败"); }
    finally { setRevisionBusy(false); }
  }

  async function approveRevision() {
    if (!activeProject || !revision || !revisionReady) return;
    setRevisionBusy(true); setMessage(""); setError("");
    try {
      const decisions = revision.proposals.map((item) => ({ proposal_id: item.proposal_id, status: decisionFor(item.proposal_id, item.review_status), note: null }));
      const response = await fetch(`/api/projects/${activeProject.project_id}/plan-revision`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ decisions, confirm: true }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "计划新版本创建失败");
      replaceProject(payload); setRevisionDecisions({}); setMessage(`Action Plan V${payload.action_plan_artifact?.version || 2} 已经人工确认并写入企业时间线。`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "计划新版本创建失败"); }
    finally { setRevisionBusy(false); }
  }

  return <main><WorkspaceHeader eyebrow="DECISION & ACTION QUALITY" title="决策与行动质量 Dashboard" description="将真实执行结果写回场景项目，持续诊断决策、计划和执行质量；任何调整都先形成建议，再由人确认。"/><section className="platformPage"><LinkedContextBar projects={projects} activeId={activeId} onChange={setActiveId}/>
    <div className="feedbackFlow">{[[`${coverage}%`,"反馈覆盖","已获得执行反馈的行动占比"],[`${averageProgress}%`,"平均进度","各行动最近一次反馈的平均进度"],[String(blockerCount),"阻塞行动","需要复核资源、假设或执行方式"],[String(entries.length),"反馈版本","保留全部历史，不覆盖旧判断"]].map((item) => <article key={item[1]}><span>{item[0]}</span><h2>{item[1]}</h2><p>{item[2]}</p></article>)}</div>
    <div className="feedbackBoard"><div><span className="eyebrow">SCENARIO-EMBEDDED FEEDBACK</span><h2>{activeProject ? `${activeProject.project_name} · 执行反馈` : "选择项目查看决策—行动—结果链路"}</h2><p>字段由 {contract?.descriptor.display_name || "当前场景"} 场景包定义。反馈会触发调整诊断，但不会静默改写已批准版本。</p></div><Link className="secondaryButton linkButton" href={activeProject ? `/projects/${activeProject.project_id}` : "/projects"}>{activeProject ? "返回场景工作流" : "选择项目"}</Link></div>
    {activeProject && actions.length > 0 ? <><div className="feedbackWorkspaceGrid"><form className="feedbackEntryForm" onSubmit={submitFeedback}><span className="eyebrow">NEW FEEDBACK</span><h2>提交本轮执行反馈</h2><label><span>行动项</span><select value={selectedActionId} onChange={(event) => setActionId(event.target.value)}>{actions.map((item) => <option key={item.action_id} value={item.action_id}>{item.title}</option>)}</select></label><label><span>完成进度 · {progressPct}%</span><input type="range" min="0" max="100" step="5" value={progressPct} onChange={(event) => setProgressPct(Number(event.target.value))}/></label><label><span>结果指标 / 事实</span><textarea value={outcomeMetrics} onChange={(event) => setOutcomeMetrics(event.target.value)} placeholder="已实现的订单、收入、客户验证、里程碑或其他可核验结果"/></label><label><span>阻塞与偏差</span><textarea value={blockers} onChange={(event) => setBlockers(event.target.value)} placeholder="没有阻塞可留空；如有，请说明原因和影响"/></label>{extraFields.map((field) => <label key={field}><span>{feedbackLabels[field] || field}</span><textarea value={scenarioFields[field] || ""} onChange={(event) => setScenarioFields((current) => ({ ...current, [field]: event.target.value }))}/></label>)}{error && <p className="formError">{error}</p>}{message && <p className="formSuccess">{message}</p>}<button className="primaryButton" disabled={saving} type="submit">{saving ? "正在写回…" : "保存反馈并更新诊断"}</button></form><section className="feedbackActionList"><span className="eyebrow">ACTION STATUS</span><h2>行动进展与最近反馈</h2>{actions.map((item) => { const feedback = latest.get(item.action_id); return <article key={item.action_id}><div><strong>{item.title}</strong><small>{item.owner_role} · {item.timing}</small></div><span>{feedback ? `${feedback.progress_pct}%` : "待反馈"}</span><p>{feedback?.outcome_metrics || "尚无执行结果记录"}</p>{feedback?.blockers && <em>阻塞：{feedback.blockers}</em>}</article>; })}</section></div>{entries.length > 0 && <section className="revisionPanel"><div className="sectionTitle"><div><span className="eyebrow">ADAPTIVE PLAN · HUMAN GATE</span><h2>偏差诊断与候选调整</h2><p>AI 只形成候选建议；原计划保持只读，全部建议经人工审核后才会创建新版本。</p></div><button className="secondaryButton" type="button" disabled={revisionBusy} onClick={() => void generateRevision()}>{revisionBusy ? "正在分析…" : revision ? "重新分析最新反馈" : "AI 分析偏差"}</button></div>{revision && <><p className="revisionSummary">{revision.summary}</p><div className="revisionTableWrap"><table><thead><tr><th>行动</th><th>偏差类型</th><th>诊断</th><th>候选调整</th><th>人工决定</th></tr></thead><tbody>{revision.proposals.map((proposal) => <tr key={proposal.proposal_id}><td>{actions.find((item) => item.action_id === proposal.action_id)?.title || proposal.action_id}</td><td>{proposal.deviation_class}</td><td>{proposal.diagnosis}<small>置信度 {proposal.confidence}%</small></td><td>{proposal.recommendation}{proposal.proposed_timing && <small>建议时序：{proposal.proposed_timing}</small>}</td><td><select value={decisionFor(proposal.proposal_id, proposal.review_status)} onChange={(event) => setRevisionDecisions((current) => ({...current, [proposal.proposal_id]: event.target.value as "needs_review" | "accepted" | "rejected"}))}><option value="needs_review">待审核</option><option value="accepted">接受调整</option><option value="rejected">维持原计划</option></select></td></tr>)}</tbody></table></div><div className="revisionApproval"><span>只有人工确认后才创建 Action Plan V{(activeProject.action_plan_artifact?.version || 1) + 1}</span><button className="primaryButton" type="button" disabled={revisionBusy || !revisionReady} onClick={() => void approveRevision()}>{revisionBusy ? "正在创建…" : "确认并创建新版本"}</button></div></>}</section>}</> : <div className="platformEmpty"><h2>尚无可反馈的已确认行动</h2><p>先在 PE、VC 或企业增长场景中完成并确认 Action Plan，反馈入口会自动出现。</p></div>}
  </section></main>;
}
