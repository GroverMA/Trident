"use client";

import { FormEvent, useMemo, useState } from "react";
import type {
  ProjectScopePayload,
  ProjectSummary,
  ResearchBriefReviewPayload,
} from "@/lib/types";

type WorkflowStep = { key: string; label: string; description: string };
type ActionState =
  | "brief-generate"
  | "brief-save"
  | "brief-confirm"
  | "plan-generate"
  | "plan-confirm"
  | "evidence-collect"
  | "evidence-save"
  | "evidence-confirm"
  | "analysis-generate"
  | "analysis-save"
  | "analysis-confirm"
  | "future-generate"
  | "future-save"
  | "future-confirm"
  | "report-generate"
  | "rewind";

const BUILD_STEPS: WorkflowStep[] = [
  { key: "prompt_analysis", label: "Prompt Analysis", description: "AI 理解原始研究需求" },
  { key: "gate_zero", label: "Gate 0 · Scope", description: "确认目标、市场边界与统计口径" },
  { key: "web_research", label: "Web Research", description: "检索并收集公开证据" },
  { key: "gate_one", label: "Gate 1 · Evidence", description: "确认来源、口径与可用性" },
  { key: "industry_analysis", label: "Industry Analysis", description: "形成市场、产业链与竞争判断" },
  { key: "future_intelligence", label: "Future Intelligence", description: "形成未来趋势、情景与反证条件" },
  { key: "gate_two", label: "Gate 2 · Content", description: "人工审核核心分析和未来判断" },
  { key: "decision_report", label: "General Report", description: "生成可追溯的完整报告" },
];

const REVIEW_STEPS: WorkflowStep[] = [
  { key: "research_brief", label: "研究范围", description: "确认报告覆盖范围与关键口径" },
  { key: "decision_report", label: "报告初稿", description: "先查看完整研究结论" },
  { key: "human_review", label: "内容修订", description: "围绕选定模块提出疑问与修改" },
  { key: "evidence_qa", label: "引用追溯", description: "检查引用来源和证据适用范围" },
  { key: "industry_analysis", label: "分析逻辑", description: "复核行业与竞争分析方法" },
  { key: "future_intelligence", label: "趋势逻辑", description: "复核预测、情景与关键假设" },
];

function stepsFor(project: ProjectSummary): WorkflowStep[] {
  const base = project.research_path === "report_review_first" ? REVIEW_STEPS : BUILD_STEPS;
  if (!project.company_strategy_enabled) return base;
  const strategy = [
    { key: "company_assessment", label: "公司评分", description: "衡量市场位置与战略目标差距" },
    { key: "action_plan", label: "行动计划", description: "形成短期与长期定制行动" },
  ];
  return project.research_path === "report_review_first"
    ? [...base, ...strategy]
    : [...base.slice(0, -1), ...strategy, base.at(-1)!];
}

function lines(value: FormDataEntryValue | null): string[] {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function errorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return "提交内容未通过结构检查，请检查必填字段。";
  }
  return fallback;
}

export function ResearchWorkspace({ initialProject }: { initialProject: ProjectSummary }) {
  const [project, setProject] = useState(initialProject);
  const [action, setAction] = useState<ActionState | null>(null);
  const [editingScope, setEditingScope] = useState(!initialProject.research_brief_artifact);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [gateZeroChecked, setGateZeroChecked] = useState(false);
  const [gateOneChecked, setGateOneChecked] = useState(false);
  const [gapAcknowledged, setGapAcknowledged] = useState(false);
  const [analysisChecked, setAnalysisChecked] = useState(false);
  const [futureChecked, setFutureChecked] = useState(false);
  const [gapResolution, setGapResolution] = useState("accept_analyst_handling");
  const [evidenceSelections, setEvidenceSelections] = useState<Record<string, "accepted" | "rejected">>(() =>
    Object.fromEntries(initialProject.evidence_collection_artifact?.task_runs.flatMap((run) =>
      run.evidence.map((item) => [
        item.evidence_id,
        item.review_status === "accepted" || item.review_status === "rejected"
          ? item.review_status
          : (item.qa_score >= 80 && item.prompt_relevance >= 0.7 ? "accepted" : "rejected"),
      ]),
    ) || []) as Record<string, "accepted" | "rejected">,
  );
  const [analysisSelections, setAnalysisSelections] = useState<Record<string, "accepted" | "rejected">>(() =>
    Object.fromEntries(initialProject.industry_analysis_artifact?.modules.flatMap((module) =>
      module.findings.flatMap((item) => item.review_status === "accepted" || item.review_status === "rejected"
        ? [[item.finding_id, item.review_status]]
        : []),
    ) || []) as Record<string, "accepted" | "rejected">,
  );
  const [futureSelections, setFutureSelections] = useState<Record<string, "accepted" | "rejected">>(() => {
    const artifact = initialProject.future_intelligence_artifact;
    return Object.fromEntries([
      ...(artifact?.trends || []).map((item) => [item.trend_id, item.review_status === "rejected" ? "rejected" : "accepted"]),
      ...(artifact?.scenarios || []).map((item) => [item.scenario_id, item.review_status === "rejected" ? "rejected" : "accepted"]),
    ]) as Record<string, "accepted" | "rejected">;
  });
  const steps = useMemo(() => stepsFor(project), [project]);
  const reviewFirst = project.research_path === "report_review_first";

  function acceptProject(result: ProjectSummary, success: string) {
    setProject(result);
    if (result.industry_analysis_artifact) {
      setAnalysisSelections(Object.fromEntries(result.industry_analysis_artifact.modules.flatMap((module) =>
        module.findings.flatMap((item) => item.review_status === "accepted" || item.review_status === "rejected"
          ? [[item.finding_id, item.review_status]]
          : []),
      )) as Record<string, "accepted" | "rejected">);
    }
    if (result.future_intelligence_artifact) {
      const artifact = result.future_intelligence_artifact;
      setFutureSelections(Object.fromEntries([
        ...artifact.trends.map((item) => [item.trend_id, item.review_status === "rejected" ? "rejected" : "accepted"]),
        ...artifact.scenarios.map((item) => [item.scenario_id, item.review_status === "rejected" ? "rejected" : "accepted"]),
      ]) as Record<string, "accepted" | "rejected">);
    }
    setMessage(success);
    setError("");
  }

  async function requestProject(path: string, method: "POST" | "PATCH", body?: unknown) {
    const response = await fetch(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = (await response.json()) as ProjectSummary & { detail?: unknown };
    if (!response.ok) {
      throw new Error(errorMessage(result.detail, "研究服务暂时未能完成本次操作。"));
    }
    return result;
  }

  async function generateBrief() {
    setAction("brief-generate");
    setMessage("");
    setError("");
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/research-brief`,
        "POST",
      );
      acceptProject(result, "AI 已完成研究简报，请核对市场边界、必答问题和待验证口径。");
      setEditingScope(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究简报暂时未能生成。");
    } finally {
      setAction(null);
    }
  }

  async function analyzePrompt(form: HTMLFormElement) {
    setAction("brief-generate");
    setMessage("");
    setError("");
    const data = new FormData(form);
    const payload: ProjectScopePayload = {
      project_name: String(data.get("project_name") || "").trim(),
      industry: String(data.get("industry") || "").trim(),
      region: String(data.get("region") || "").trim(),
      research_objective: String(data.get("research_objective") || "").trim(),
      time_horizon: String(data.get("time_horizon") || "").trim(),
      output_language: String(data.get("output_language") || "简体中文"),
      target_company: project.target_company || null,
      company_strategy_objective: project.company_strategy_objective || null,
      confirm: false,
    };
    try {
      await requestProject(`/api/projects/${project.project_id}`, "PATCH", payload);
      const result = await requestProject(
        `/api/projects/${project.project_id}/research-brief`,
        "POST",
      );
      acceptProject(result, "AI 已完成 Prompt Analysis。请逐项检查并修改研究范围，再确认 Gate 0。");
      setEditingScope(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "AI 暂时未能完成 Prompt Analysis。");
    } finally {
      setAction(null);
    }
  }

  async function reviewBrief(form: HTMLFormElement, confirm: boolean) {
    const brief = project.research_brief_artifact;
    if (!brief) return;
    setAction(confirm ? "brief-confirm" : "brief-save");
    setMessage("");
    setError("");
    const data = new FormData(form);
    const clarificationQuestions = brief.clarification_questions.map((question, index) =>
      String(data.get(`clarification_question_${index}`) || question).trim(),
    ).filter(Boolean);
    const clarificationResponses = Object.fromEntries(
      clarificationQuestions.map((question, index) => [
        question,
        String(data.get(`clarification_response_${index}`) || "").trim(),
      ]),
    );
    const payload: ResearchBriefReviewPayload = {
      decision_statement: String(data.get("decision_statement") || "").trim(),
      market_definition: {
        core_market: String(data.get("core_market") || "").trim(),
        product_scope: String(data.get("product_scope") || "").trim(),
        customer_scope: String(data.get("customer_scope") || "").trim(),
        geography_scope: String(data.get("geography_scope") || "").trim(),
        value_chain_scope: String(data.get("value_chain_scope") || "").trim(),
        time_scope: String(data.get("time_scope") || "").trim(),
        inclusions: lines(data.get("inclusions")),
        exclusions: lines(data.get("exclusions")),
        market_sizing_basis: String(data.get("market_sizing_basis") || "尚待明确").trim(),
        competitor_definition: String(data.get("competitor_definition") || "").trim(),
        adjacent_markets: lines(data.get("adjacent_markets")),
        ambiguities: lines(data.get("ambiguities")),
      },
      key_questions: lines(data.get("key_questions")),
      information_gaps: lines(data.get("information_gaps")),
      hypotheses: lines(data.get("hypotheses")),
      clarification_questions: clarificationQuestions,
      clarification_responses: clarificationResponses,
      confidence_note: String(data.get("confidence_note") || "").trim(),
      confirm,
    };
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/research-brief`,
        "PATCH",
        payload,
      );
      acceptProject(
        result,
        confirm
          ? "研究简报已确认，AI 可以据此拆解研究任务和校验节点。"
          : "研究简报草稿已保存到云端。",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究简报未能保存。");
    } finally {
      setAction(null);
    }
  }

  async function generatePlan() {
    setAction("plan-generate");
    setMessage("");
    setError("");
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/research-plan`,
        "POST",
      );
      acceptProject(result, "研究计划已经生成。请确认任务、信息需求和人工校验节点。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究计划暂时未能生成。");
    } finally {
      setAction(null);
    }
  }

  async function confirmPlan() {
    setAction("plan-confirm");
    setMessage("");
    setError("");
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/research-plan`,
        "PATCH",
        { confirm: true },
      );
      acceptProject(
        result,
        reviewFirst
          ? "研究底稿已经确认，项目已具备生成报告初稿的完整任务结构。"
          : "研究计划已经确认，项目已进入网页证据研究节点。",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究计划暂时未能确认。");
    } finally {
      setAction(null);
    }
  }

  async function collectEvidence() {
    setAction("evidence-collect");
    setMessage("");
    setError("");
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/evidence`,
        "POST",
        {},
      );
      const artifact = result.evidence_collection_artifact;
      if (artifact) {
        setEvidenceSelections(Object.fromEntries(artifact.task_runs.flatMap((run) =>
          run.evidence.map((item) => [
            item.evidence_id,
            item.qa_score >= 80 && item.prompt_relevance >= 0.7 ? "accepted" : "rejected",
          ]),
        )) as Record<string, "accepted" | "rejected">);
      }
      acceptProject(result, "网页检索和证据结构化已经完成，请逐条接受或拒绝候选证据。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "网页证据研究暂时未能完成。");
    } finally {
      setAction(null);
    }
  }

  async function reviewEvidence(form: HTMLFormElement, confirm: boolean) {
    const artifact = project.evidence_collection_artifact;
    if (!artifact) return;
    setAction(confirm ? "evidence-confirm" : "evidence-save");
    setMessage("");
    setError("");
    const data = new FormData(form);
    const decisions = artifact.task_runs.flatMap((run) =>
      run.evidence.flatMap((item) => {
        const status = evidenceSelections[item.evidence_id] || String(data.get(`evidence_status_${item.evidence_id}`) || "");
        if (status !== "accepted" && status !== "rejected") return [];
        return [{
          evidence_id: item.evidence_id,
          status,
          note: String(data.get(`evidence_note_${item.evidence_id}`) || "").trim() || null,
        }];
      }),
    );
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/evidence`,
        "PATCH",
        {
          decisions,
          confirm,
          coverage_gap_resolution: gapResolution,
          coverage_gap_user_input: String(data.get("coverage_gap_user_input") || "").trim() || null,
          coverage_gaps_acknowledged: gapAcknowledged,
        },
      );
      acceptProject(
        result,
        confirm
          ? "Gate 1 已确认，项目可以进入行业分析。"
          : "证据审核决定已经保存。",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "证据审核未能保存。");
    } finally {
      setAction(null);
    }
  }

  async function rewindWorkflow() {
    setAction("rewind");
    setMessage("");
    setError("");
    try {
      const response = await fetch(`/api/projects/${project.project_id}/rewind`, { method: "POST" });
      const result = await response.json() as { project?: ProjectSummary; message?: string; detail?: unknown };
      if (!response.ok || !result.project) throw new Error(errorMessage(result.detail, "暂时无法返回上一审核节点。"));
      setProject(result.project);
      setMessage(result.message || "已返回上一审核节点。");
      setEditingScope(false);
      setGateZeroChecked(false);
      setGateOneChecked(false);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "暂时无法返回上一审核节点。");
    } finally {
      setAction(null);
    }
  }

  async function generateIndustryAnalysis() {
    setAction("analysis-generate");
    setMessage("");
    setError("");
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/industry-analysis`,
        "POST",
      );
      acceptProject(result, "五个行业分析模块已经生成，请逐项审核判断、机制、证据和适用边界。");
      setAnalysisChecked(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "行业分析暂时未能生成。");
    } finally {
      setAction(null);
    }
  }

  async function reviewIndustryAnalysis(form: HTMLFormElement, confirm: boolean) {
    const artifact = project.industry_analysis_artifact;
    if (!artifact) return;
    setAction(confirm ? "analysis-confirm" : "analysis-save");
    setMessage("");
    setError("");
    const data = new FormData(form);
    const decisions = artifact.modules.flatMap((module) => module.findings.flatMap((item) => {
      const status = analysisSelections[item.finding_id];
      if (status !== "accepted" && status !== "rejected") return [];
      return [{
        finding_id: item.finding_id,
        status,
        note: String(data.get(`analysis_note_${item.finding_id}`) || "").trim() || null,
      }];
    }));
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}/industry-analysis`,
        "PATCH",
        { decisions, confirm },
      );
      acceptProject(
        result,
        confirm ? "行业分析已经人工确认，Future Intelligence 节点已开放。" : "行业判断审核决定已经保存。",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "行业分析审核未能保存。");
    } finally {
      setAction(null);
    }
  }

  async function generateFutureIntelligence() {
    setAction("future-generate"); setMessage(""); setError("");
    try {
      const result = await requestProject(`/api/projects/${project.project_id}/future-intelligence`, "POST");
      acceptProject(result, "Future Intelligence 已生成，请审核趋势、情景、领先指标和反证条件。");
      setFutureChecked(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Future Intelligence 暂时未能生成。");
    } finally { setAction(null); }
  }

  async function reviewFutureIntelligence(form: HTMLFormElement, confirm: boolean) {
    const artifact = project.future_intelligence_artifact;
    if (!artifact) return;
    setAction(confirm ? "future-confirm" : "future-save"); setMessage(""); setError("");
    const data = new FormData(form);
    const items = [...artifact.trends.map((item) => item.trend_id), ...artifact.scenarios.map((item) => item.scenario_id)];
    const decisions = items.flatMap((itemId) => {
      const status = futureSelections[itemId];
      return status === "accepted" || status === "rejected" ? [{ item_id: itemId, status, note: String(data.get(`future_note_${itemId}`) || "").trim() || null }] : [];
    });
    try {
      const result = await requestProject(`/api/projects/${project.project_id}/future-intelligence`, "PATCH", { decisions, confirm });
      acceptProject(result, confirm ? "Future Intelligence 已确认，Gate 2 内容审核节点已经开放。" : "趋势与情景审核决定已经保存。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Future Intelligence 审核未能保存。");
    } finally { setAction(null); }
  }

  async function generateGeneralReport() {
    setAction("report-generate"); setMessage(""); setError("");
    try {
      const result = await requestProject(`/api/projects/${project.project_id}/general-report`, "POST");
      acceptProject(result, "Gate 2 已完成，General Report 已根据批准内容生成。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "General Report 暂时未能生成，已审核内容不会丢失。");
    } finally { setAction(null); }
  }

  function selectEvidence(mode: "recommended" | "all" | "none") {
    const artifact = project.evidence_collection_artifact;
    if (!artifact) return;
    setEvidenceSelections(Object.fromEntries(artifact.task_runs.flatMap((run) =>
      run.evidence.map((item) => [
        item.evidence_id,
        mode === "all" || (mode === "recommended" && item.qa_score >= 80 && item.prompt_relevance >= 0.7)
          ? "accepted"
          : "rejected",
      ]),
    )) as Record<string, "accepted" | "rejected">);
  }

  const brief = project.research_brief_artifact;
  const plan = project.research_plan_artifact;
  const evidence = project.evidence_collection_artifact;
  const analysis = project.industry_analysis_artifact;
  const future = project.future_intelligence_artifact;
  const report = project.general_report_artifact;
  const analysisFindings = analysis?.modules.flatMap((module) => module.findings) || [];
  const evidenceAdvisories = plan && evidence ? plan.tasks.flatMap((task) => {
    const run = evidence.task_runs.find((item) => item.task_id === task.task_id);
    const candidates = run?.evidence.filter((item) => item.qa_score >= 80 && item.prompt_relevance >= 0.7) || [];
    const covered = new Set(candidates.flatMap((item) => item.question_ids || []));
    const coveredPrompts = new Set(candidates.flatMap((item) => item.prompt_question_ids || []));
    if (candidates.length && !candidates.some((item) => item.question_ids?.length)) {
      task.questions.forEach((_question, index) => covered.add(`${task.task_id}-Q${index + 1}`));
    }
    if (candidates.length && !candidates.some((item) => item.prompt_question_ids?.length)) {
      task.prompt_question_ids.forEach((id) => coveredPrompts.add(id));
    }
    const missing = candidates.length ? task.questions.flatMap((question, index) => {
      const id = `${task.task_id}-Q${index + 1}`;
      return covered.has(id) ? [] : [`${id}：${question}`];
    }) : [`没有同时达到质量分80和Prompt相关性70%的证据`];
    missing.push(...task.prompt_question_ids.filter((id) => !coveredPrompts.has(id)).map((id) => `用户必答问题${id}尚无高质量直接证据`));
    const issues = [...missing, ...(run?.search_errors || [])];
    return issues.length ? [{
      taskId: task.task_id,
      priority: issues.some((item) => item.includes("用户必答问题")) ? "核心问题重点审阅" : "一般重点审阅",
      issue: issues.join("；"),
      recommendation: "现有材料将按证据边界形成限制性结论，并在报告中标注部分回答与建议补数路径。",
    }] : [];
  }) : [];
  const canRewind = Boolean(
    brief?.human_confirmed || plan || evidence || project.workflow_status.industry_analysis === "completed",
  );
  const buildStepDone: Record<string, boolean> = {
    prompt_analysis: Boolean(brief),
    gate_zero: Boolean(brief?.human_confirmed),
    web_research: Boolean(evidence),
    gate_one: Boolean(evidence?.human_confirmed),
    industry_analysis: project.workflow_status.industry_analysis === "completed",
    future_intelligence: project.workflow_status.future_intelligence === "completed",
    gate_two: project.workflow_status.human_review === "completed",
    decision_report: project.workflow_status.decision_report === "completed",
  };
  const completed = reviewFirst
    ? steps.filter((step) => project.workflow_status[step.key] === "completed").length
    : BUILD_STEPS.filter((step) => buildStepDone[step.key]).length;

  return (
    <main className="workflowCanvas">
      <div className="workspaceTags"><span>General Research</span><span>{project.industry}</span><span>{project.region}</span><span>No Industry Pack</span></div>
      <header className="studioHeading">
        <div className="eyebrow">RESEARCH STUDIO · THREE HUMAN GATES</div>
        <h1>行业研究工作台</h1>
        <p>通用报告与高级分析师模式可以相互切换，且已经完成的研究部分不会丢失</p>
      </header>
      <div className="workspaceMode"><span>工作模式</span><div><button className="active" type="button">快速通用报告</button><button type="button">高级分析师工作台</button></div><p>快速通用报告：依次确认市场口径、网页证据和报告内容，其他步骤自动衔接。</p></div>

      <section className="workflowSection" aria-label="研究进度">
        <div className="workflowSummary">
          <div>
            <span>研究进度</span>
            <strong>{completed}/{steps.length} 个节点已完成</strong>
          </div>
          <span>最后保存 {new Date(project.updated_at).toLocaleString("zh-CN")}</span>
        </div>
        <div className="workflowTrack">
          {steps.map((step, index) => {
            const done = !reviewFirst && buildStepDone[step.key];
            const status = done ? "completed" : (project.workflow_status[step.key] || "not_started");
            const active = !done && index === completed;
            return (
              <div
                className={`workflowNode workflowNode-${status} ${active ? "workflowNodeActive" : ""}`}
                key={step.key}
                title={step.description}
              >
                <div className="workflowDot">{index + 1}</div>
                <strong>{step.label}</strong>
              </div>
            );
          })}
        </div>
      </section>

      {canRewind && !reviewFirst && (
        <section className="rewindPanel">
          <div><strong>需要修改前序内容？</strong><span>返回最近的人工审核节点后，已保存的前序资料会保留；该节点之后不再有效的分析、趋势或报告会被清除。</span></div>
          <small>{evidence?.human_confirmed ? "将返回 Gate 1 证据审核。" : "将返回 Gate 0 市场口径；确认修改后需要重新执行研究。"}</small>
          <button type="button" className="secondaryButton" disabled={action !== null} onClick={() => void rewindWorkflow()}>{action === "rewind" ? "正在返回…" : "← 返回上一审核节点"}</button>
        </section>
      )}

      {!editingScope ? (
        project.market_scope_confirmed_at ? <section className="confirmedScopeBar">
          <div>
            <span className="eyebrow">CONFIRMED SCOPE</span>
            <strong>{project.industry} · {project.region} · {project.time_horizon}</strong>
          </div>
          <button className="secondaryButton" type="button" onClick={() => setEditingScope(true)}>
            修改研究范围
          </button>
        </section> : null
      ) : (
        <section className="scopePanel">
          <div className="scopeIntro">
            <div>
              <span className="eyebrow">PROMPT ANALYSIS</span>
              <h2>研究目标与执行边界</h2>
              <p>第一步只调用语言模型理解原始 Prompt 并生成市场描述，不会立即搜索网页。</p>
            </div>
            <div className="scopePathNote">
              <strong>{reviewFirst ? "自上而下审阅" : "自下而上构建"}</strong>
              <span>{reviewFirst ? "范围 → 初稿 → 逻辑 → 证据" : "范围 → 规划 → 证据 → 分析 → 报告"}</span>
            </div>
          </div>
          <form
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              void analyzePrompt(event.currentTarget);
            }}
          >
            <input type="hidden" name="project_name" value={project.project_name} />
            <input type="hidden" name="industry" value={project.industry} />
            <input type="hidden" name="region" value={project.region} />
            <input type="hidden" name="research_objective" value={project.research_objective} />
            <input type="hidden" name="time_horizon" value={project.time_horizon} />
            <input type="hidden" name="output_language" value={project.output_language} />
            <details className="researchBoundary" open>
              <summary>研究目标与执行边界</summary>
              <div><p><strong>行业：</strong>{project.industry} · <strong>地区：</strong>{project.region}</p><p><strong>研究目标：</strong>{project.research_objective}</p><p><strong>时间范围：</strong>{project.time_horizon}</p><small>第一步只调用语言模型理解原始Prompt并生成市场描述，不会立即搜索网页。</small></div>
            </details>
            {project.company_strategy_enabled && (
              <div className="strategyContext">
                <span>企业战略决策支持</span>
                <strong>{project.target_company}</strong>
                <p>{project.company_strategy_objective}</p>
              </div>
            )}
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            <div className="scopeActions singleAction">
              <button type="submit" className="primaryButton" disabled={action !== null}>
                {action === "brief-generate" ? "AI 正在理解原始 Prompt，并形成可审阅的市场描述与研究口径…" : "AI分析研究需求并生成市场描述"}
              </button>
            </div>
          </form>
        </section>
      )}

      {project.market_scope_confirmed_at && !editingScope && !brief && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">AI RESEARCH BRIEF</span>
          <h2>{reviewFirst ? "生成报告准备底稿" : "生成结构化研究简报"}</h2>
          <p>
            {reviewFirst
              ? "AI 会先把研究范围转化为可追溯的必答问题、市场口径和验证假设，为完整初稿做准备。"
              : "AI 会按照统一研究方法解释你的 Prompt，形成市场定义、必答问题、信息缺口和待验证假设。"}
          </p>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          <button
            className="primaryButton artifactPrimary"
            type="button"
            disabled={action !== null}
            onClick={() => void generateBrief()}
          >
            {action === "brief-generate"
              ? "AI 正在分析研究需求…"
              : reviewFirst
                ? "生成报告准备底稿"
                : "AI 生成研究简报"}
          </button>
        </section>
      )}

      {brief && !brief.human_confirmed && (
        <section className="artifactPanel">
          <div className="artifactHeading">
            <div>
              <h2>Gate 0 · 对齐AI对研究问题和市场口径的理解</h2>
              <p>AI已经根据你的原始Prompt生成市场描述。请修改任何不准确的定义；确认后的版本将成为检索、分析、趋势和报告的共同口径。</p>
            </div>
          </div>
          <section className="promptInterpretation">
            <h3>用户原始Prompt</h3>
            <p>{brief.original_prompt || project.research_objective}</p>
            {brief.interpreted_intent && Object.keys(brief.interpreted_intent.terminology_map).length > 0 && <><strong>AI术语理解</strong><ul>{Object.entries(brief.interpreted_intent.terminology_map).map(([term, meaning]) => <li key={term}>{term} → {meaning}</li>)}</ul></>}
          </section>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (gateZeroChecked) void reviewBrief(event.currentTarget, true);
            }}
          >
            <label className="field fieldWide">
              <span>AI理解后的研究目标</span>
              <textarea name="decision_statement" required rows={4} defaultValue={brief.decision_statement} />
            </label>
            <label className="field fieldWide"><span>最终报告必须回答的问题（每行一项）</span><textarea name="key_questions" required rows={7} defaultValue={brief.key_questions.join("\n")} /></label>
            <h3 className="formSectionTitle">市场描述与统计口径</h3>
            <div className="fieldGrid">
              <label className="field fieldWide"><span>核心市场定义</span><textarea name="core_market" required rows={3} defaultValue={brief.market_definition.core_market} /></label>
            </div>
            <div className="fieldGrid">
              <label className="field"><span>产品/服务范围</span><textarea name="product_scope" required rows={4} defaultValue={brief.market_definition.product_scope} /></label>
              <label className="field"><span>客户与应用范围</span><textarea name="customer_scope" required rows={4} defaultValue={brief.market_definition.customer_scope} /></label>
              <label className="field"><span>地理范围</span><input name="geography_scope" required defaultValue={brief.market_definition.geography_scope} /></label>
              <label className="field"><span>时间范围</span><input name="time_scope" required defaultValue={brief.market_definition.time_scope} /></label>
            </div>
            <label className="field fieldWide"><span>价值链范围</span><textarea name="value_chain_scope" required rows={4} defaultValue={brief.market_definition.value_chain_scope} /></label>
            <label className="field fieldWide"><span>市场规模统计口径</span><textarea name="market_sizing_basis" rows={4} defaultValue={brief.market_definition.market_sizing_basis} /></label>
            <label className="field fieldWide"><span>竞争者与可比公司识别口径</span><textarea name="competitor_definition" required rows={4} defaultValue={brief.market_definition.competitor_definition} /></label>
            <div className="fieldGrid">
              <label className="field"><span>纳入范围（每行一项）</span><textarea name="inclusions" required rows={6} defaultValue={brief.market_definition.inclusions.join("\n")} /></label>
              <label className="field"><span>排除范围（每行一项）</span><textarea name="exclusions" required rows={6} defaultValue={brief.market_definition.exclusions.join("\n")} /></label>
            </div>
            <label className="field fieldWide"><span>相邻但不属于核心市场的领域（每行一项）</span><textarea name="adjacent_markets" rows={5} defaultValue={brief.market_definition.adjacent_markets.join("\n")} /></label>
            <label className="field fieldWide"><span>仍需验证的市场口径（每行一项）</span><textarea name="ambiguities" rows={5} defaultValue={brief.market_definition.ambiguities.join("\n")} /></label>
            <div className="fieldGrid">
              <label className="field"><span>当前信息缺口（每行一项）</span><textarea name="information_gaps" required rows={6} defaultValue={brief.information_gaps.join("\n")} /></label>
              <label className="field"><span>待验证假设（每行一项）</span><textarea name="hypotheses" required rows={6} defaultValue={brief.hypotheses.join("\n")} /></label>
            </div>
            {brief.clarification_questions.length > 0 && (
              <div className="clarificationBlock">
                <div className="clarificationIntro"><h3>仍需在研究中验证的口径问题</h3><p>左侧为AI识别的待验证问题，右侧为研究者的对应确认口径。问题和回答均可修改。</p></div>
                {brief.clarification_questions.map((question, index) => (
                  <div className="clarificationRow" key={`${index}-${question}`}>
                    <label className="field"><span>待确认问题 {index + 1}</span><textarea name={`clarification_question_${index}`} rows={3} defaultValue={question} /></label>
                    <label className="field"><span>研究者确认口径 {index + 1}</span><textarea name={`clarification_response_${index}`} rows={3} defaultValue={brief.clarification_responses[question] || ""} placeholder="在这里输入明确口径；暂不确定时可说明采用的默认假设。" /></label>
                  </div>
                ))}
              </div>
            )}
            <label className="field fieldWide"><span>当前置信度说明</span><textarea name="confidence_note" required rows={3} defaultValue={brief.confidence_note} /></label>
            <label className="gateConfirmation"><input type="checkbox" checked={gateZeroChecked} onChange={(event) => setGateZeroChecked(event.target.checked)} /><span>我已核对并确认上述市场定义、纳入排除范围和报告必答问题</span></label>
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            <div className="scopeActions">
              <button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewBrief(form, false); }}>{action === "brief-save" ? "正在保存…" : "保存简报草稿"}</button>
              <button className="primaryButton" type="submit" disabled={action !== null || !gateZeroChecked}>{action === "brief-confirm" ? "正在确认…" : "确认Gate 0并开始网页研究"}</button>
            </div>
          </form>
        </section>
      )}

      {brief?.human_confirmed && !plan && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">RESEARCH PLANNING</span>
          <h2>{reviewFirst ? "形成可追溯报告底稿" : "拆解研究任务与校验节点"}</h2>
          <p>{reviewFirst ? "这一步在后台明确报告初稿需要完成的研究任务、来源要求和反证条件，随后即可进入报告生成。" : "AI 将把已确认的必答问题拆解成研究任务，并为每项任务规定证据标准、反证要求和人工校验节点。"}</p>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void generatePlan()}>{action === "plan-generate" ? "AI 正在拆解研究任务…" : reviewFirst ? "生成可追溯报告底稿" : "AI 生成研究计划"}</button>
        </section>
      )}

      {plan && (
        <section className="artifactPanel">
          <div className="artifactHeading">
            <div><span className="eyebrow">RESEARCH PLAN</span><h2>{plan.human_confirmed ? "研究计划已经确认" : "检查任务拆解与人工校验节点"}</h2><p>{plan.plan_summary}</p></div>
            <span className={plan.human_confirmed ? "confirmedLabel" : "reviewRequired"}>{plan.human_confirmed ? "已确认" : "人工确认 · 必选"}</span>
          </div>
          <div className="planStats"><div><span>研究任务</span><strong>{plan.tasks.length}</strong></div><div><span>人工校验节点</span><strong>{plan.human_review_gates.length}</strong></div><div><span>待补充口径</span><strong>{plan.unresolved_gaps.length}</strong></div></div>
          <div className="taskList">
            {plan.tasks.map((task) => (
              <details className="taskCard" key={task.task_id}>
                <summary><span>{task.task_id}</span><strong>{task.title}</strong><small>{task.validation_gate}</small></summary>
                <div className="taskBody">
                  <p>{task.objective}</p>
                  <div className="taskColumns">
                    <div><h4>研究问题</h4><ul>{task.questions.map((item) => <li key={item}>{item}</li>)}</ul></div>
                    <div><h4>信息需求</h4><ul>{task.information_needs.map((item) => <li key={item}>{item}</li>)}</ul></div>
                    <div><h4>优先来源</h4><ul>{task.preferred_sources.map((item) => <li key={item}>{item}</li>)}</ul></div>
                  </div>
                  <div className="evidenceStandard"><strong>证据标准</strong><span>{task.evidence_standard}</span></div>
                </div>
              </details>
            ))}
          </div>
          <div className="planReviewGrid">
            <div><h3>人工校验节点</h3><ul>{plan.human_review_gates.map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div><h3>仍需在研究中验证</h3>{plan.unresolved_gaps.length ? <ul>{plan.unresolved_gaps.map((item) => <li key={item}>{item}</li>)}</ul> : <p>当前没有未记录的口径缺口。</p>}</div>
          </div>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          {!plan.human_confirmed ? (
            <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void confirmPlan()}>{action === "plan-confirm" ? "正在确认…" : reviewFirst ? "确认底稿并进入报告初稿" : "确认计划并进入网页研究"}</button>
          ) : (
            <div className="nextStageNotice"><strong>{reviewFirst ? "报告初稿节点已经就绪" : "网页证据研究节点已经就绪"}</strong><span>{reviewFirst ? "下一阶段将接入完整报告编排、引用追溯与内容修订工作台。" : "下一阶段将接入搜索、抓取、证据结构化与批量人工审核。"}</span></div>
          )}
        </section>
      )}

      {!reviewFirst && plan?.human_confirmed && !evidence && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">EVIDENCE COLLECTION</span>
          <h2>执行网页研究并建立证据矩阵</h2>
          <p>系统将按照已确认的 Research Plan 搜索、抓取和结构化来源。候选内容不会自动成为报告证据，必须经过人工接受。</p>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void collectEvidence()}>
            {action === "evidence-collect" ? "正在检索和核验证据…" : "开始网页证据研究"}
          </button>
        </section>
      )}

      {!reviewFirst && evidence && (
        <section className="artifactPanel">
          {evidenceAdvisories.length > 0 && !evidence.human_confirmed && <section className="evidenceGapPanel">
            <h2>证据缺口与分析师处理建议</h2>
            <p>本轮检索未完全覆盖 AI 拆解出的所有问题，但证据缺口不会阻断研究。后续分析会降低相关结论置信度，并在报告中明确标注证据边界。</p>
            <div className="evidenceTableWrap"><table className="evidenceTable"><thead><tr><th>任务</th><th>缺口类型</th><th>相对缺失的问题</th><th>分析师处理建议</th></tr></thead><tbody>{evidenceAdvisories.map((item) => <tr key={item.taskId}><td>{item.taskId}</td><td>{item.priority}</td><td>{item.issue}</td><td>{item.recommendation}</td></tr>)}</tbody></table></div>
            <fieldset className="gapResolution"><legend>如何处理本轮证据缺口</legend><label><input type="radio" name="gap_resolution" checked={gapResolution === "accept_analyst_handling"} onChange={() => setGapResolution("accept_analyst_handling")} />接受分析师处理建议并带限制继续</label><label><input type="radio" name="gap_resolution" checked={gapResolution === "user_input"} onChange={() => setGapResolution("user_input")} />补充我的判断后继续</label></fieldset>
            {gapResolution === "user_input" && <label className="field"><span>补充你的行业判断、内部观察或建议采用的口径</span><textarea name="coverage_gap_user_input" form="gate-one-form" rows={4} /></label>}
            <label className="gateConfirmation requiredConfirmation"><input type="checkbox" checked={gapAcknowledged} onChange={(event) => setGapAcknowledged(event.target.checked)} /><span>我已阅读上述缺口及处理方式，并确认可以在这些证据边界下继续研究（必选）</span></label>
          </section>}
          <div className="artifactHeading">
            <div>
              <span className="eyebrow">GATE 1 · EVIDENCE REVIEW</span>
              <h2>{evidence.human_confirmed ? "证据矩阵已经确认" : "逐条审核候选证据"}</h2>
              <p>接受表示该陈述可进入后续分析；拒绝表示保留审计记录但不用于形成判断。</p>
            </div>
            <span className={evidence.human_confirmed ? "confirmedLabel" : "reviewRequired"}>{evidence.human_confirmed ? "已确认" : "人工确认 · 必选"}</span>
          </div>
          <form id="gate-one-form" onSubmit={(event) => { event.preventDefault(); if (gateOneChecked) void reviewEvidence(event.currentTarget, true); }}>
            {!evidence.human_confirmed && <div className="evidenceBulkActions"><button type="button" className="secondaryButton" onClick={() => selectEvidence("recommended")}>采用全部系统推荐</button><button type="button" className="secondaryButton" onClick={() => selectEvidence("all")}>一键全选</button><button type="button" className="secondaryButton" onClick={() => selectEvidence("none")}>全部取消</button></div>}
            <div className="taskList">
              {evidence.task_runs.map((run) => (
                <details className="taskCard" key={run.run_id} open>
                  <summary><span>{run.task_id}</span><strong>{run.task_title}</strong><small>{run.evidence.length} 条候选证据</small></summary>
                  <div className="taskBody">
                    {run.evidence.map((item) => {
                      const source = run.sources.find((candidate) => candidate.source_id === item.source_id);
                      return (
                        <div className="evidenceStandard" key={item.evidence_id}>
                          <strong>{item.kind} · QA {item.qa_score}</strong>
                          <span>{item.statement}</span>
                          <small>{item.supporting_excerpt}</small>
                          {source && <a href={source.url} target="_blank" rel="noreferrer">{source.title} · {source.domain}</a>}
                          {!evidence.human_confirmed && (
                            <div className="fieldGrid">
                              <label className="field"><span>审核决定</span><select name={`evidence_status_${item.evidence_id}`} value={evidenceSelections[item.evidence_id] || ""} onChange={(event) => setEvidenceSelections((current) => ({ ...current, [item.evidence_id]: event.target.value as "accepted" | "rejected" }))}><option value="">待决定</option><option value="accepted">接受</option><option value="rejected">拒绝</option></select></label>
                              <label className="field"><span>审核备注</span><input name={`evidence_note_${item.evidence_id}`} defaultValue={item.reviewer_note || ""} /></label>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {run.information_gaps.length > 0 && <div><h4>仍有信息缺口</h4><ul>{run.information_gaps.map((item) => <li key={item}>{item}</li>)}</ul></div>}
                  </div>
                </details>
              ))}
            </div>
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            {!evidence.human_confirmed && (
              <><label className="gateConfirmation requiredConfirmation"><input type="checkbox" checked={gateOneChecked} onChange={(event) => setGateOneChecked(event.target.checked)} /><span>我已检查拟采用证据的来源、原文和适用范围，并确认其可用于本次研究（必选）</span></label><div className="scopeActions">
                <button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewEvidence(form, false); }}>{action === "evidence-save" ? "正在保存…" : "保存审核决定"}</button>
                <button type="submit" className="primaryButton" disabled={action !== null || !gateOneChecked || (evidenceAdvisories.length > 0 && !gapAcknowledged)}>{action === "evidence-confirm" ? "正在确认…" : "确认 Gate 1 并进入行业分析"}</button>
              </div></>
            )}
          </form>
        </section>
      )}

      {!reviewFirst && evidence?.human_confirmed && !analysis && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">INDUSTRY ANALYSIS</span>
          <h2>生成当前行业分析</h2>
          <p>系统只使用 Gate 1 已接受证据，依次形成行业定义与价值链、市场现状、竞争格局、驱动与制约以及商业逻辑；本节点不生成未来预测。</p>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void generateIndustryAnalysis()}>
            {action === "analysis-generate" ? "AI 正在生成五个行业分析模块…" : "AI 生成行业分析"}
          </button>
        </section>
      )}

      {!reviewFirst && analysis && (
        <section className="artifactPanel">
          <div className="artifactHeading">
            <div><span className="eyebrow">INDUSTRY ANALYSIS · HUMAN REVIEW</span><h2>{analysis.human_confirmed ? "当前行业分析已经确认" : "逐项审核行业判断"}</h2><p>事实综合、来源观点、分析师推断和商业判断保持分层；拒绝的判断保留审计记录但不会进入趋势或报告。</p></div>
            <span className={analysis.human_confirmed ? "confirmedLabel" : "reviewRequired"}>{analysis.human_confirmed ? "已确认" : "人工确认 · 必选"}</span>
          </div>
          <div className="planStats"><div><span>使用证据</span><strong>{analysis.input_evidence_ids.length}</strong></div><div><span>分析模块</span><strong>{analysis.modules.length}</strong></div><div><span>行业判断</span><strong>{analysisFindings.length}</strong></div><div><span>已接受判断</span><strong>{analysisFindings.filter((item) => item.review_status === "accepted").length}</strong></div></div>
          <form onSubmit={(event) => { event.preventDefault(); if (analysisChecked) void reviewIndustryAnalysis(event.currentTarget, true); }}>
            <div className="taskList">
              {analysis.modules.map((module, moduleIndex) => (
                <details className="taskCard" key={module.module_id} open={moduleIndex === 0}>
                  <summary><span>{moduleIndex + 1}</span><strong>{module.title}</strong><small>{module.findings.length} 项判断</small></summary>
                  <div className="taskBody">
                    <p>{module.executive_summary}</p>
                    {module.evidence_gaps.length > 0 && <div className="analysisBoundary"><strong>证据缺口</strong><ul>{module.evidence_gaps.map((item) => <li key={item}>{item}</li>)}</ul></div>}
                    {module.rejected_questions.length > 0 && <div className="analysisBoundary"><strong>当前证据无法回答</strong><ul>{module.rejected_questions.map((item) => <li key={item}>{item}</li>)}</ul></div>}
                    {module.findings.map((item) => (
                      <article className="analysisFinding" key={item.finding_id}>
                        <div className="analysisFindingHeader"><div><span>{item.finding_type.replaceAll("_", " ")}</span><strong>{item.subject}</strong></div><b>{Math.round(item.confidence * 100)}% 置信度</b></div>
                        <h3>{item.statement}</h3>
                        <p><strong>判断机制：</strong>{item.mechanism}</p>
                        {Object.keys(item.comparison_dimensions).length > 0 && <dl className="analysisDimensions">{Object.entries(item.comparison_dimensions).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>}
                        <div className="analysisMeta"><span>适用范围：{item.scope}</span><span>不确定性：{item.uncertainty}</span><span>失效条件：{item.boundary_condition}</span><span>Evidence：{item.evidence_ids.join("、")}</span></div>
                        {!analysis.human_confirmed && <div className="fieldGrid"><label className="field"><span>审核决定</span><select value={analysisSelections[item.finding_id] || ""} onChange={(event) => setAnalysisSelections((current) => ({ ...current, [item.finding_id]: event.target.value as "accepted" | "rejected" }))}><option value="">待决定</option><option value="accepted">接受并进入后续研究</option><option value="rejected">拒绝但保留审计记录</option></select></label><label className="field"><span>审核备注</span><input name={`analysis_note_${item.finding_id}`} defaultValue={item.reviewer_note || ""} /></label></div>}
                      </article>
                    ))}
                  </div>
                </details>
              ))}
            </div>
            {analysis.cross_module_conflicts.length > 0 && <div className="evidenceGapPanel"><h3>跨模块冲突</h3><ul>{analysis.cross_module_conflicts.map((item) => <li key={item}>{item}</li>)}</ul></div>}
            {analysis.overall_evidence_limitations.length > 0 && <div className="analysisBoundary"><h3>整体证据边界</h3><ul>{analysis.overall_evidence_limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>}
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            {!analysis.human_confirmed && <><label className="gateConfirmation requiredConfirmation"><input type="checkbox" checked={analysisChecked} onChange={(event) => setAnalysisChecked(event.target.checked)} /><span>我已逐项审核所有行业判断、证据引用、适用范围和不确定性（必选）</span></label><div className="scopeActions"><button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewIndustryAnalysis(form, false); }}>{action === "analysis-save" ? "正在保存…" : "保存审核决定"}</button><button type="submit" className="primaryButton" disabled={action !== null || !analysisChecked || analysisFindings.some((item) => !analysisSelections[item.finding_id])}>{action === "analysis-confirm" ? "正在确认…" : "批准行业分析并进入 Future Intelligence"}</button></div></>}
            {analysis.human_confirmed && !future && <div className="nextStageNotice"><strong>Future Intelligence 节点已经就绪</strong><span>将严格继承已确认行业定义、规模、竞争与驱动因素 Skill，生成可证伪趋势和三种情景。</span></div>}
          </form>
        </section>
      )}

      {!reviewFirst && analysis?.human_confirmed && !future && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">FUTURE INTELLIGENCE</span>
          <h2>生成未来趋势与情景</h2>
          <p>系统只使用已接受证据和行业判断，形成历史机制、未来趋势、玩家动作、基准/加速/受阻情景、领先指标与反证条件，不输出伪精确概率。</p>
          {message && <div className="formSuccess" role="status">{message}</div>}
          {error && <div className="formError" role="alert">{error}</div>}
          <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void generateFutureIntelligence()}>{action === "future-generate" ? "AI 正在构建趋势与情景…" : "AI 生成 Future Intelligence"}</button>
        </section>
      )}

      {!reviewFirst && future && (
        <section className="artifactPanel">
          <div className="artifactHeading"><div><span className="eyebrow">FUTURE INTELLIGENCE · HUMAN REVIEW</span><h2>{future.human_confirmed ? "未来趋势与情景已经确认" : "审核趋势、情景与反证条件"}</h2><p>每项判断均保留因果链、证据、领先指标和失效条件；拒绝项不会进入最终报告。</p></div><span className={future.human_confirmed ? "confirmedLabel" : "reviewRequired"}>{future.human_confirmed ? "已确认" : "人工确认 · 必选"}</span></div>
          <div className="planStats"><div><span>趋势</span><strong>{future.trends.length}</strong></div><div><span>情景</span><strong>{future.scenarios.length}</strong></div><div><span>已接受</span><strong>{[...future.trends, ...future.scenarios].filter((item) => item.review_status === "accepted").length}</strong></div><div><span>预测方法</span><strong>{future.forecast_methodology.quantitative_forecast_used ? "量化" : "因果情景"}</strong></div></div>
          <div className="analysisBoundary"><strong>方法选择：{future.forecast_methodology.selected_method}</strong><p>{future.forecast_methodology.selection_rationale}</p><small>{future.forecast_methodology.validation_design}</small></div>
          <form onSubmit={(event) => { event.preventDefault(); if (futureChecked) void reviewFutureIntelligence(event.currentTarget, true); }}>
            <div className="taskList">
              {future.trends.map((item, index) => <details className="taskCard" key={item.trend_id} open={index === 0}><summary><span>T{index + 1}</span><strong>{item.title}</strong><small>{item.confidence.overall}% 置信度</small></summary><div className="taskBody"><article className="analysisFinding"><h3>{item.forecast_statement}</h3><p><strong>因果机制：</strong>{item.causal_mechanism.join(" → ")}</p><div className="analysisMeta"><span>市场规模净影响：{item.market_size_net_impact_score}</span><span>盈利能力净影响：{item.profitability_net_impact_score}</span><span>Evidence：{item.evidence_ids.join("、")}</span></div><div className="fieldGrid"><div className="analysisBoundary"><strong>领先指标</strong><ul>{item.leading_indicators.map((indicator) => <li key={indicator.name}>{indicator.name}：{indicator.trigger_condition}</li>)}</ul></div><div className="analysisBoundary"><strong>反证条件</strong><ul>{item.falsification_conditions.map((condition) => <li key={condition}>{condition}</li>)}</ul></div></div>{!future.human_confirmed && <div className="fieldGrid"><label className="field"><span>审核决定</span><select value={futureSelections[item.trend_id] || ""} onChange={(event) => setFutureSelections((current) => ({ ...current, [item.trend_id]: event.target.value as "accepted" | "rejected" }))}><option value="">待决定</option><option value="accepted">接受并进入报告</option><option value="rejected">拒绝但保留记录</option></select></label><label className="field"><span>审核备注</span><input name={`future_note_${item.trend_id}`} defaultValue={item.reviewer_note || ""} /></label></div>}</article></div></details>)}
              {future.scenarios.map((item) => <details className="taskCard" key={item.scenario_id}><summary><span>{item.scenario_type}</span><strong>{item.title}</strong><small>情景</small></summary><div className="taskBody"><p>{item.narrative}</p><div className="fieldGrid"><div><strong>触发条件</strong><ul>{item.trigger_conditions.map((condition) => <li key={condition}>{condition}</li>)}</ul></div><div><strong>预期结果</strong><ul>{item.expected_outcomes.map((outcome) => <li key={outcome}>{outcome}</li>)}</ul></div></div>{!future.human_confirmed && <div className="fieldGrid"><label className="field"><span>审核决定</span><select value={futureSelections[item.scenario_id] || ""} onChange={(event) => setFutureSelections((current) => ({ ...current, [item.scenario_id]: event.target.value as "accepted" | "rejected" }))}><option value="">待决定</option><option value="accepted">接受</option><option value="rejected">拒绝</option></select></label><label className="field"><span>审核备注</span><input name={`future_note_${item.scenario_id}`} defaultValue={item.reviewer_note || ""} /></label></div>}</div></details>)}
            </div>
            {future.forecast_gaps.length > 0 && <div className="evidenceGapPanel"><h3>预测证据缺口</h3><ul>{future.forecast_gaps.map((item) => <li key={item}>{item}</li>)}</ul></div>}
            {message && <div className="formSuccess" role="status">{message}</div>}{error && <div className="formError" role="alert">{error}</div>}
            {!future.human_confirmed && <><div className="nextStageNotice"><strong>默认采用全部未明确拒绝的内容</strong><span>你只需把不希望进入报告的趋势或情景改为“拒绝”，无需逐项重复确认。</span></div><label className="gateConfirmation requiredConfirmation"><input type="checkbox" checked={futureChecked} onChange={(event) => setFutureChecked(event.target.checked)} /><span>我已审阅拟进入报告的趋势、情景、风险和局限（必选）</span></label><div className="scopeActions"><button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewFutureIntelligence(form, false); }}>{action === "future-save" ? "正在保存…" : "保存排除项"}</button><button type="submit" className="primaryButton" disabled={action !== null || !futureChecked}>{action === "future-confirm" ? "正在确认…" : "确认 Future Intelligence 并进入 Gate 2"}</button></div></>}
            {future.human_confirmed && <div className="nextStageNotice"><strong>Gate 2 内容审核已经就绪</strong><span>已批准趋势和情景将与行业分析共同进入报告内容审核。</span></div>}
          </form>
        </section>
      )}

      {!reviewFirst && future?.human_confirmed && !report && (
        <section className="artifactPanel artifactStart">
          <span className="eyebrow">GATE 2 · CONTENT</span><h2>确认内容并生成 General Report</h2>
          <p>行业判断、趋势和情景已经完成内容选择。报告只组合已批准材料，生成失败不会清除任何审核结果，可以安全重试。</p>
          {message && <div className="formSuccess" role="status">{message}</div>}{error && <div className="formError" role="alert">{error}</div>}
          <button className="primaryButton artifactPrimary" type="button" disabled={action !== null} onClick={() => void generateGeneralReport()}>{action === "report-generate" ? "AI 正在组织完整报告…" : "确认 Gate 2 并生成 General Report"}</button>
        </section>
      )}

      {!reviewFirst && report && (
        <section className="artifactPanel"><div className="artifactHeading"><div><span className="eyebrow">GENERAL REPORT</span><h2>{report.title}</h2><p>{report.source_count} 个来源 · {report.accepted_finding_ids.length} 项行业判断 · {report.accepted_trend_ids.length} 项趋势</p></div><span className="confirmedLabel">报告已生成</span></div>{report.unresolved_prompt_questions.length > 0 && <div className="evidenceGapPanel"><h3>仍未完全回答的问题</h3><ul>{report.unresolved_prompt_questions.map((item) => <li key={item}>{item}</li>)}</ul></div>}<article className="reportMarkdown"><pre>{report.markdown}</pre></article></section>
      )}
    </main>
  );
}
