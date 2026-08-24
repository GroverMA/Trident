"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { ProjectSummary, SensingSignal } from "@/lib/types";

const ACTIVE_PROJECT_KEY = "trident_active_project_id";
const categories: Record<string, string> = {
  policy: "政策", competition: "竞争", customer: "客户",
  technology: "技术", operations: "经营 KPI", other: "其他",
};
const impacts: Record<string, string> = { high: "高影响", medium: "中影响", review: "待评估" };
const assets: Record<string, string> = {
  research_scope: "研究范围与假设", company_scorecard: "Company Scorecard", action_plan: "Action Plan",
};

export function ContinuousSensingWorkspace() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeId, setActiveId] = useState("");
  const [filter, setFilter] = useState("全部");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const active = projects.find((project) => project.project_id === activeId);
  const artifact = active?.continuous_sensing_artifact;
  const signals = artifact?.signals || [];
  const watchTerms = drafts[activeId] ?? (artifact?.watch_terms || []).join("、");
  const visible = filter === "全部" ? signals : signals.filter((signal) => categories[signal.category] === filter);

  useEffect(() => {
    fetch("/api/projects", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then((rows: ProjectSummary[]) => {
        setProjects(rows);
        const saved = window.localStorage.getItem(ACTIVE_PROJECT_KEY);
        setActiveId(saved && rows.some((row) => row.project_id === saved) ? saved : (rows[0]?.project_id || ""));
      })
      .catch(() => setProjects([]));
  }, []);

  function selectProject(projectId: string) {
    setActiveId(projectId);
    window.localStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
  }

  function replaceProject(project: ProjectSummary) {
    setProjects((current) => current.map((item) => item.project_id === project.project_id ? project : item));
  }

  async function refresh() {
    if (!active) return;
    setBusy("refresh"); setError("");
    try {
      const terms = watchTerms.split(/[、,，\n]/).map((item) => item.trim()).filter(Boolean);
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ watch_terms: terms, feed_urls: [] }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "新闻抓取失败");
      replaceProject(payload);
      setDrafts((current) => ({ ...current, [active.project_id]: payload.continuous_sensing_artifact?.watch_terms?.join("、") || watchTerms }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "新闻抓取失败"); }
    finally { setBusy(""); }
  }

  async function review(signal: SensingSignal, status: "accepted" | "ignored") {
    if (!active) return;
    setBusy(signal.signal_id); setError("");
    try {
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing`, {
        method: "PATCH", headers: { "content-type": "application/json" },
        body: JSON.stringify({ signal_id: signal.signal_id, status, note: "" }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "信号审核失败");
      replaceProject(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "信号审核失败"); }
    finally { setBusy(""); }
  }

  const today = new Date().toDateString();
  const todayCount = signals.filter((signal) => new Date(signal.published_at || signal.captured_at).toDateString() === today).length;
  const acceptedCount = signals.filter((signal) => signal.review_status === "accepted").length;
  const pendingCount = signals.filter((signal) => signal.review_status === "needs_review").length;

  return <main>
    <header className="consultingTopbar"><div><span>TRIDENT AI</span><strong>Decision Intelligence Studio</strong></div><nav><Link href="/">场景选择</Link><Link href="/projects">项目管理</Link></nav></header>
    <div className="platformPageHero"><span className="eyebrow">CONTINUOUS SENSING</span><h1>持续感知与决策信号</h1><p>真实抓取公司与行业新闻，先形成可追溯信号，再由人工决定是否进入决策复核。</p></div>
    <section className="platformPage">
      <div className="linkedContext"><div><span>当前联动项目</span><strong>{active?.project_name || "尚未选择项目"}</strong><small>{active ? `${active.target_company || active.industry} · ${active.region}` : "先在项目管理中选择工作项目"}</small></div><select value={activeId} onChange={(event) => selectProject(event.target.value)}><option value="">选择项目</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)}</select><nav><Link href="/knowledge">知识库</Link><Link href="/feedback">质量 Dashboard</Link>{active && <Link href={`/projects/${active.project_id}`}>研究工作台</Link>}</nav></div>
      <div className="sensingSubscription"><div><span className="eyebrow">WATCH TERMS</span><h2>公司与行业关注词</h2><p>默认来自项目公司、行业、地区和市场范围；可补充竞争者、技术、客户或政策主题。</p></div><label><span>关注词（逗号分隔）</span><input value={watchTerms} onChange={(event) => setDrafts((current) => ({ ...current, [activeId]: event.target.value }))} placeholder="公司、行业、竞争者、技术主题"/></label><button className="primaryButton" disabled={!active || busy === "refresh"} onClick={() => void refresh()}>{busy === "refresh" ? "正在抓取并去重…" : "立即刷新新闻"}</button>{error && <p className="formError">{error}</p>}{artifact?.fetch_errors?.length ? <p className="sensingWarning">部分来源暂不可用：{artifact.fetch_errors.join("；")}。历史信号和其他来源不受影响。</p> : null}</div>
      <div className="sensingSummary"><article><span>{todayCount}</span><small>今日新增</small></article><article><span>{signals.length}</span><small>累计信号</small></article><article><span>{pendingCount}</span><small>待人工复核</small></article><article><span>{acceptedCount}</span><small>已接受并路由</small></article></div>
      <div className="sensingLayout"><section className="signalFeed"><div className="sectionTitle"><div><span className="eyebrow">SIGNAL INBOX</span><h2>新闻与变化信号</h2></div><small>{artifact ? `更新于 ${new Date(artifact.refreshed_at).toLocaleString("zh-CN")}` : "尚未刷新"}</small></div><div className="signalFilters">{["全部", "政策", "竞争", "客户", "技术", "经营 KPI", "其他"].map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item}</button>)}</div>
        {visible.map((signal) => <article className="signalReviewCard" key={signal.signal_id}><header><span>{categories[signal.category]}</span><em className={`impact-${signal.impact}`}>{impacts[signal.impact]}</em><small>相关性 {signal.relevance_score}</small></header><a href={signal.url} target="_blank" rel="noreferrer"><h3>{signal.title}</h3></a><p>{signal.summary || signal.impact_reason}</p><div className="signalSource">{signal.source} · {new Date(signal.published_at || signal.captured_at).toLocaleString("zh-CN")} · 命中 {signal.matched_terms.join("、")}</div>{signal.assessment && <div className="signalAssessment"><strong>候选影响分析</strong><p>{signal.assessment.recommended_review}</p><small>关联：{signal.assessment.affected_assets.map((item) => assets[item] || item).join("、")} · 置信度 {signal.assessment.confidence}</small>{signal.assessment.affected_hypotheses.length > 0 && <details><summary>可能受影响的研究假设</summary><ul>{signal.assessment.affected_hypotheses.map((item) => <li key={item}>{item}</li>)}</ul></details>}</div>}<footer><span className={`reviewStatus ${signal.review_status}`}>{signal.review_status === "accepted" ? "已接受并写入时间线" : signal.review_status === "ignored" ? "已忽略" : "等待人工判断"}</span><div><button className="secondaryButton" disabled={busy === signal.signal_id} onClick={() => void review(signal, "ignored")}>忽略</button><button className="primaryButton" disabled={busy === signal.signal_id} onClick={() => void review(signal, "accepted")}>接受并评估影响</button></div></footer></article>)}
        {!visible.length && <div className="platformEmpty"><h2>{active ? "尚无匹配信号" : "请先选择联动项目"}</h2><p>{active ? "确认关注词后刷新，系统将保存与该项目相关的真实公开新闻。" : "不同企业和投资标的的信号分别保存。"}</p></div>}
      </section><aside className="impactPanel"><span className="eyebrow">HUMAN-GOVERNED ROUTER</span><h2>信号不会直接改写决策</h2><ol><li><span>01</span><div><strong>抓取、清理和去重</strong><small>保留来源链接与发布时间</small></div></li><li><span>02</span><div><strong>项目与实体匹配</strong><small>按公司、行业和关注主题关联</small></div></li><li><span>03</span><div><strong>人工接受或忽略</strong><small>接受后才生成候选影响分析</small></div></li><li><span>04</span><div><strong>进入后续复核</strong><small>只写时间线，不覆盖报告或计划</small></div></li></ol><Link className="primaryButton linkButton" href={active ? `/projects/${active.project_id}` : "/projects"}>回到项目处理影响</Link></aside></div>
    </section>
  </main>;
}
