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
const taskTargets: Record<string, string> = {
  research_scope: "研究范围", company_scorecard: "Company Scorecard", action_plan: "Action Plan",
};

export function ContinuousSensingWorkspace() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeId, setActiveId] = useState("");
  const [filter, setFilter] = useState("全部");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceType, setSourceType] = useState<"company_official" | "regulator_government" | "exchange_disclosure" | "professional_media">("company_official");
  const [sourceFormat, setSourceFormat] = useState<"auto" | "rss" | "html">("auto");
  const active = projects.find((project) => project.project_id === activeId);
  const artifact = active?.continuous_sensing_artifact;
  const signals = artifact?.signals || [];
  const reviewTasks = artifact?.review_tasks || [];
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
      const registeredSources = artifact?.sources || [];
      const sources = sourceUrl.trim() ? [...registeredSources, {
        name: sourceType === "company_official" ? "公司官方" : sourceType === "regulator_government" ? "政府/监管" : sourceType === "exchange_disclosure" ? "交易所披露" : "专业媒体",
        source_type: sourceType,
        source_format: sourceFormat,
        tier: sourceType === "professional_media" ? 2 : 1,
        url: sourceUrl.trim(), enabled: true,
      }] : registeredSources;
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ watch_terms: terms, feed_urls: [], sources }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "新闻抓取失败");
      replaceProject(payload);
      setSourceUrl("");
      setDrafts((current) => ({ ...current, [active.project_id]: payload.continuous_sensing_artifact?.watch_terms?.join("、") || watchTerms }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "新闻抓取失败"); }
    finally { setBusy(""); }
  }

  async function saveSubscription(cadence: "manual" | "daily" | "weekly") {
    if (!active) return;
    setBusy("subscription"); setError("");
    try {
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing/subscription`, {
        method: "PUT", headers: { "content-type": "application/json" },
        body: JSON.stringify({ enabled: cadence !== "manual", cadence }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "订阅设置保存失败");
      replaceProject(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "订阅设置保存失败"); }
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

  async function reviewTask(taskId: string, status: "approved_for_revision" | "dismissed") {
    if (!active) return;
    setBusy(taskId); setError("");
    try {
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing/review-task`, {
        method: "PATCH", headers: { "content-type": "application/json" },
        body: JSON.stringify({ task_id: taskId, status, note: "" }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "影响复核失败");
      replaceProject(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "影响复核失败"); }
    finally { setBusy(""); }
  }

  async function reviewCandidate(taskId: string, status: "approved" | "rejected") {
    if (!active) return;
    setBusy(`candidate-${taskId}`); setError("");
    try {
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing/candidate-gate`, {
        method: "PATCH", headers: { "content-type": "application/json" },
        body: JSON.stringify({ task_id: taskId, status, note: "" }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "候选版本审核失败");
      replaceProject(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "候选版本审核失败"); }
    finally { setBusy(""); }
  }

  async function reviewAsset(taskId: string, status: "activated" | "rejected") {
    if (!active) return;
    setBusy(`asset-${taskId}`); setError("");
    try {
      const response = await fetch(`/api/projects/${active.project_id}/continuous-sensing/asset-gate`, {
        method: "PATCH", headers: { "content-type": "application/json" },
        body: JSON.stringify({ task_id: taskId, status, note: "" }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "资产版本审核失败");
      replaceProject(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "资产版本审核失败"); }
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
      <div className="sensingSubscription"><div><span className="eyebrow">WATCH TERMS</span><h2>公司、行业与一手来源</h2><p>关注词用于发现变化；可登记已获授权的公司官网、监管、交易所或专业媒体网页/RSS。一手来源优先进入审核队列。</p></div><label><span>关注词（逗号分隔）</span><input value={watchTerms} onChange={(event) => setDrafts((current) => ({ ...current, [activeId]: event.target.value }))} placeholder="公司、行业、竞争者、技术主题"/></label><label><span>自动感知频率</span><select value={artifact?.subscription?.enabled ? artifact.subscription.cadence : "manual"} disabled={!active || busy === "subscription"} onChange={(event) => void saveSubscription(event.target.value as "manual" | "daily" | "weekly")}><option value="manual">仅手动刷新</option><option value="daily">每日</option><option value="weekly">每周</option></select></label><label><span>新增来源类型</span><select value={sourceType} onChange={(event) => setSourceType(event.target.value as typeof sourceType)}><option value="company_official">公司官方</option><option value="regulator_government">政府/监管</option><option value="exchange_disclosure">交易所披露</option><option value="professional_media">专业媒体</option></select></label><label><span>来源格式</span><select value={sourceFormat} onChange={(event) => setSourceFormat(event.target.value as typeof sourceFormat)}><option value="auto">自动识别</option><option value="html">网页公告列表</option><option value="rss">RSS</option></select></label><label><span>来源地址（HTTPS）</span><input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://example.com/news"/></label><button className="primaryButton" disabled={!active || busy === "refresh"} onClick={() => void refresh()}>{busy === "refresh" ? "正在抓取并去重…" : sourceUrl ? "保存来源并刷新" : "立即刷新新闻"}</button>{artifact?.subscription?.next_run_at && <p className="sensingSchedule">下次自动运行：{new Date(artifact.subscription.next_run_at).toLocaleString("zh-CN")}</p>}{artifact?.sources?.length ? <div className="sensingSources">{artifact.sources.map((source) => <span key={source.source_id} className={`source-${source.status}`}>{source.name} · {source.source_format.toUpperCase()} · Tier {source.tier} · {source.status === "succeeded" ? "连接成功" : source.status === "failed" ? "连接失败" : "待检查"}</span>)}</div> : null}{error && <p className="formError">{error}</p>}{artifact?.fetch_errors?.length ? <p className="sensingWarning">部分来源暂不可用：{artifact.fetch_errors.join("；")}。历史信号和其他来源不受影响。</p> : null}</div>
      {artifact?.management_digest && <div className="sensingDigest"><div><span className="eyebrow">MANAGEMENT DIGEST</span><h2>{artifact.management_digest.headline}</h2></div><p>{artifact.management_digest.summary}</p><small>本轮新增 {artifact.management_digest.new_signal_count} · 高影响 {artifact.management_digest.high_impact_count} · 待复核 {artifact.management_digest.pending_review_count}</small></div>}
      <div className="sensingSummary"><article><span>{todayCount}</span><small>今日新增</small></article><article><span>{signals.length}</span><small>累计信号</small></article><article><span>{pendingCount}</span><small>待人工复核</small></article><article><span>{acceptedCount}</span><small>已接受并路由</small></article></div>
      <div className="sensingLayout"><section className="signalFeed"><div className="sectionTitle"><div><span className="eyebrow">SIGNAL INBOX</span><h2>新闻与变化信号</h2></div><small>{artifact ? `更新于 ${new Date(artifact.refreshed_at).toLocaleString("zh-CN")}` : "尚未刷新"}</small></div><div className="signalFilters">{["全部", "政策", "竞争", "客户", "技术", "经营 KPI", "其他"].map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item}</button>)}</div>
        {visible.map((signal) => <article className="signalReviewCard" key={signal.signal_id}><header><span>{categories[signal.category]}</span><em className={`impact-${signal.impact}`}>{impacts[signal.impact]}</em><small>Tier {signal.source_tier} · 相关性 {signal.relevance_score}</small></header><a href={signal.url} target="_blank" rel="noreferrer"><h3>{signal.title}</h3></a><p>{signal.summary || signal.impact_reason}</p><div className="signalSource">{signal.source} · {new Date(signal.published_at || signal.captured_at).toLocaleString("zh-CN")} · 命中 {signal.matched_terms.join("、")}</div>{signal.assessment && <div className="signalAssessment"><strong>候选影响分析</strong><p>{signal.assessment.recommended_review}</p><small>关联：{signal.assessment.affected_assets.map((item) => assets[item] || item).join("、")} · 置信度 {signal.assessment.confidence}</small>{signal.assessment.affected_hypotheses.length > 0 && <details><summary>可能受影响的研究假设</summary><ul>{signal.assessment.affected_hypotheses.map((item) => <li key={item}>{item}</li>)}</ul></details>}</div>}<footer><span className={`reviewStatus ${signal.review_status}`}>{signal.review_status === "accepted" ? "已接受并写入时间线" : signal.review_status === "ignored" ? "已忽略" : "等待人工判断"}</span><div><button className="secondaryButton" disabled={busy === signal.signal_id} onClick={() => void review(signal, "ignored")}>忽略</button><button className="primaryButton" disabled={busy === signal.signal_id} onClick={() => void review(signal, "accepted")}>接受并评估影响</button></div></footer></article>)}
        {!visible.length && <div className="platformEmpty"><h2>{active ? "尚无匹配信号" : "请先选择联动项目"}</h2><p>{active ? "确认关注词后刷新，系统将保存与该项目相关的真实公开新闻。" : "不同企业和投资标的的信号分别保存。"}</p></div>}
      </section><aside className="impactPanel"><span className="eyebrow">HUMAN-GOVERNED ROUTER</span><h2>信号不会直接改写决策</h2><ol><li><span>01</span><div><strong>抓取、清理和去重</strong><small>保留来源链接与发布时间</small></div></li><li><span>02</span><div><strong>项目与实体匹配</strong><small>按公司、行业和关注主题关联</small></div></li><li><span>03</span><div><strong>人工接受或忽略</strong><small>接受后生成版本化影响复核任务</small></div></li><li><span>04</span><div><strong>两级版本 Gate</strong><small>先批准候选方向，再审核完整资产草稿</small></div></li></ol><div className="impactTaskList"><h3>版本化影响复核</h3>{reviewTasks.map((task) => <article key={task.task_id}><header><strong>{taskTargets[task.target]}</strong><span>候选 V{task.proposed_version}</span></header><p>{task.recommended_review}</p><small>{task.base_artifact_id ? `基于 ${task.base_artifact_id}${task.base_version ? ` · V${task.base_version}` : ""}` : "尚无基准资产，将进入首版复核"}</small>{task.status === "needs_review" ? <footer><button className="secondaryButton" disabled={busy === task.task_id} onClick={() => void reviewTask(task.task_id, "dismissed")}>关闭</button><button className="primaryButton" disabled={busy === task.task_id} onClick={() => void reviewTask(task.task_id, "approved_for_revision")}>批准生成候选版</button></footer> : <em>{task.status === "approved_for_revision" ? "已生成候选修订" : "已关闭"}</em>}{task.candidate && <div className="revisionCandidate"><div><strong>{task.candidate.title}</strong><small>{task.candidate.scenario_id}@{task.candidate.scenario_version}</small></div><p>{task.candidate.rationale}</p><h4>候选变更</h4><ul>{task.candidate.proposed_changes.map((item) => <li key={item}>{item}</li>)}</ul><details><summary>不可变约束与方法来源</summary><ul>{task.candidate.retained_constraints.map((item) => <li key={item}>{item}</li>)}</ul><small>Skills：{Object.entries(task.candidate.skill_versions).map(([id, version]) => `${id}@${version}`).join("、") || "场景契约与研究 SOP"}</small></details>{task.candidate.gate_status === "needs_review" ? <footer><button className="secondaryButton" disabled={busy === `candidate-${task.task_id}`} onClick={() => void reviewCandidate(task.task_id, "rejected")}>退回候选版</button><button className="primaryButton" disabled={busy === `candidate-${task.task_id}`} onClick={() => void reviewCandidate(task.task_id, "approved")}>通过候选 Gate 并生成资产草稿</button></footer> : <em>{task.candidate.gate_status === "approved" ? "候选方向已通过，完整资产草稿如下" : "候选版本已退回"}</em>}{task.candidate.asset_draft && <div className="assetVersionDraft"><header><strong>完整资产 V{task.candidate.asset_draft.proposed_version}</strong><small>{task.candidate.asset_draft.proposed_artifact_id}</small></header><p>旧版本仍在使用；以下草稿通过结构校验，但不会在最终资产 Gate 前生效。</p><h4>相对基准版本的变化</h4><ul>{task.candidate.asset_draft.change_summary.map((item) => <li key={item}>{item}</li>)}</ul><details><summary>完整资产内容与校验结果</summary><pre>{JSON.stringify(task.candidate.asset_draft.artifact_payload, null, 2)}</pre><ul>{task.candidate.asset_draft.validation_checks.map((item) => <li key={item}>{item}</li>)}</ul></details>{task.candidate.asset_draft.gate_status === "needs_review" ? <footer><button className="secondaryButton" disabled={busy === `asset-${task.task_id}`} onClick={() => void reviewAsset(task.task_id, "rejected")}>退回资产草稿</button><button className="primaryButton" disabled={busy === `asset-${task.task_id}`} onClick={() => void reviewAsset(task.task_id, "activated")}>批准并切换至 V{task.candidate.asset_draft.proposed_version}</button></footer> : <em>{task.candidate.asset_draft.gate_status === "activated" ? "新版本已启用，旧版本已进入历史" : "资产草稿已退回，当前版本保持不变"}</em>}</div>}</div>}</article>)}{!reviewTasks.length && <p className="impactTaskEmpty">接受一条新闻后，系统会按当前项目阶段生成复核任务。</p>}</div><Link className="primaryButton linkButton" href={active ? `/projects/${active.project_id}` : "/projects"}>回到项目处理影响</Link></aside></div>
    </section>
  </main>;
}
