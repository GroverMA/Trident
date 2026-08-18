"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type {
  ProjectScopePayload,
  ProjectSummary,
  ResearchBriefReviewPayload,
} from "@/lib/types";

type WorkflowStep = { key: string; label: string; description: string };
type ActionState =
  | "scope-draft"
  | "scope-confirm"
  | "brief-generate"
  | "brief-save"
  | "brief-confirm"
  | "plan-generate"
  | "plan-confirm"
  | "evidence-collect"
  | "evidence-save"
  | "evidence-confirm";

const BUILD_STEPS: WorkflowStep[] = [
  { key: "research_brief", label: "研究范围", description: "确认目标、市场边界与时间口径" },
  { key: "research_planning", label: "研究规划", description: "拆解问题、信息需求和校验节点" },
  { key: "evidence_collection", label: "网页研究", description: "检索并收集公开证据" },
  { key: "evidence_qa", label: "证据审核", description: "确认来源、口径与可用性" },
  { key: "industry_analysis", label: "行业分析", description: "形成市场、产业链与竞争判断" },
  { key: "future_intelligence", label: "趋势预测", description: "形成未来趋势、情景与反证条件" },
  { key: "decision_report", label: "研究报告", description: "生成可追溯的完整报告" },
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

function statusLabel(status: string | undefined): string {
  const labels: Record<string, string> = {
    completed: "已完成",
    ready: "可开始",
    in_progress: "进行中",
    needs_review: "待确认",
    blocked: "需处理",
    not_applicable: "不适用",
    not_started: "待开始",
  };
  return labels[status || "not_started"] || "待开始";
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
  const router = useRouter();
  const [project, setProject] = useState(initialProject);
  const [action, setAction] = useState<ActionState | null>(null);
  const [editingScope, setEditingScope] = useState(!initialProject.market_scope_confirmed_at);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const steps = useMemo(() => stepsFor(project), [project]);
  const reviewFirst = project.research_path === "report_review_first";

  function acceptProject(result: ProjectSummary, success: string) {
    setProject(result);
    setMessage(success);
    setError("");
    router.refresh();
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

  async function updateScope(form: HTMLFormElement, confirm: boolean) {
    setAction(confirm ? "scope-confirm" : "scope-draft");
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
      confirm,
    };
    try {
      const result = await requestProject(
        `/api/projects/${project.project_id}`,
        "PATCH",
        payload,
      );
      acceptProject(
        result,
        confirm
          ? "研究范围已确认，下一步由 AI 形成结构化研究简报。"
          : "研究范围草稿已保存到云端。",
      );
      if (confirm) setEditingScope(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究范围未能保存，请稍后重试。");
    } finally {
      setAction(null);
    }
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
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究简报暂时未能生成。");
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
    const clarificationResponses = Object.fromEntries(
      brief.clarification_questions.map((question, index) => [
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
        adjacent_markets: brief.market_definition.adjacent_markets,
        ambiguities: brief.market_definition.ambiguities,
      },
      key_questions: lines(data.get("key_questions")),
      information_gaps: lines(data.get("information_gaps")),
      hypotheses: lines(data.get("hypotheses")),
      clarification_questions: brief.clarification_questions,
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
        const status = String(data.get(`evidence_status_${item.evidence_id}`) || "");
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
        { decisions, confirm },
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

  const completed = steps.filter(
    (step) => project.workflow_status[step.key] === "completed",
  ).length;
  const brief = project.research_brief_artifact;
  const plan = project.research_plan_artifact;
  const evidence = project.evidence_collection_artifact;

  return (
    <main className="workflowCanvas">
      <div className="projectHeading">
        <div>
          <div className="badge badgeAccent">{reviewFirst ? "审阅式研究" : "构建式研究"}</div>
          <h1>{project.project_name}</h1>
          <p>{project.research_objective}</p>
        </div>
        <div className="cloudState">
          <span>云端项目</span>
          <strong>
            {project.market_scope_confirmed_at ? "研究范围已确认" : "研究范围待确认"}
          </strong>
        </div>
      </div>

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
            const status = project.workflow_status[step.key] || "not_started";
            const active = project.current_step === step.key;
            return (
              <div
                className={`workflowNode workflowNode-${status} ${active ? "workflowNodeActive" : ""}`}
                key={step.key}
                title={step.description}
              >
                <div className="workflowDot">{index + 1}</div>
                <strong>{step.label}</strong>
                <span>{statusLabel(status)}</span>
              </div>
            );
          })}
        </div>
      </section>

      {project.market_scope_confirmed_at && !editingScope ? (
        <section className="confirmedScopeBar">
          <div>
            <span className="eyebrow">CONFIRMED SCOPE</span>
            <strong>{project.industry} · {project.region} · {project.time_horizon}</strong>
          </div>
          <button className="secondaryButton" type="button" onClick={() => setEditingScope(true)}>
            修改研究范围
          </button>
        </section>
      ) : (
        <section className="scopePanel">
          <div className="scopeIntro">
            <div>
              <span className="eyebrow">SCOPE GATE</span>
              <h2>确认研究目标与市场范围</h2>
              <p>这里决定后续检索、分析和报告使用的统一口径。保存草稿不会推进流程；确认后会进入下一节点。</p>
            </div>
            <div className="scopePathNote">
              <strong>{reviewFirst ? "自上而下审阅" : "自下而上构建"}</strong>
              <span>{reviewFirst ? "范围 → 初稿 → 逻辑 → 证据" : "范围 → 规划 → 证据 → 分析 → 报告"}</span>
            </div>
          </div>
          <form
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              void updateScope(event.currentTarget, true);
            }}
          >
            <label className="field fieldWide">
              <span>项目名称</span>
              <input name="project_name" required defaultValue={project.project_name} />
            </label>
            <div className="fieldGrid">
              <label className="field">
                <span>行业</span>
                <input name="industry" required defaultValue={project.industry} />
              </label>
              <label className="field">
                <span>国家或地区</span>
                <input name="region" required defaultValue={project.region} />
              </label>
            </div>
            <label className="field fieldWide scopePrompt">
              <span>核心研究目标（主要 Prompt）</span>
              <textarea
                name="research_objective"
                required
                rows={7}
                defaultValue={project.research_objective}
              />
            </label>
            <div className="fieldGrid">
              <label className="field">
                <span>时间范围</span>
                <input name="time_horizon" required defaultValue={project.time_horizon} />
              </label>
              <label className="field">
                <span>输出语言</span>
                <select name="output_language" defaultValue={project.output_language}>
                  <option>简体中文</option>
                  <option>English</option>
                  <option>中英双语</option>
                </select>
              </label>
            </div>
            {project.company_strategy_enabled && (
              <div className="strategyContext">
                <span>企业战略决策支持</span>
                <strong>{project.target_company}</strong>
                <p>{project.company_strategy_objective}</p>
              </div>
            )}
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            <div className="scopeActions">
              <button
                type="button"
                className="secondaryButton"
                disabled={action !== null}
                onClick={(event) => {
                  const form = event.currentTarget.form;
                  if (form) void updateScope(form, false);
                }}
              >
                {action === "scope-draft" ? "正在保存…" : "保存范围草稿"}
              </button>
              <button type="submit" className="primaryButton" disabled={action !== null}>
                {action === "scope-confirm"
                  ? "正在确认…"
                  : reviewFirst
                    ? "确认范围并准备报告底稿"
                    : "确认范围并进入研究规划"}
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
              <span className="eyebrow">HUMAN REVIEW</span>
              <h2>核对 AI 对研究问题的理解</h2>
              <p>所有字段都可修改。确认后，这份简报将成为后续任务拆解和报告生成的统一依据。</p>
            </div>
            <span className="reviewRequired">人工确认 · 必选</span>
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void reviewBrief(event.currentTarget, true);
            }}
          >
            <label className="field fieldWide scopePrompt">
              <span>本次研究需要支持的核心判断</span>
              <textarea name="decision_statement" required rows={4} defaultValue={brief.decision_statement} />
            </label>
            <h3 className="formSectionTitle">市场定义与边界</h3>
            <div className="fieldGrid">
              <label className="field"><span>核心市场</span><input name="core_market" required defaultValue={brief.market_definition.core_market} /></label>
              <label className="field"><span>产品与服务范围</span><input name="product_scope" required defaultValue={brief.market_definition.product_scope} /></label>
              <label className="field"><span>客户范围</span><input name="customer_scope" required defaultValue={brief.market_definition.customer_scope} /></label>
              <label className="field"><span>地理范围</span><input name="geography_scope" required defaultValue={brief.market_definition.geography_scope} /></label>
              <label className="field"><span>产业链范围</span><input name="value_chain_scope" required defaultValue={brief.market_definition.value_chain_scope} /></label>
              <label className="field"><span>时间范围</span><input name="time_scope" required defaultValue={brief.market_definition.time_scope} /></label>
            </div>
            <div className="fieldGrid">
              <label className="field"><span>纳入范围（每行一项）</span><textarea name="inclusions" required rows={6} defaultValue={brief.market_definition.inclusions.join("\n")} /></label>
              <label className="field"><span>排除范围（每行一项）</span><textarea name="exclusions" required rows={6} defaultValue={brief.market_definition.exclusions.join("\n")} /></label>
            </div>
            <label className="field fieldWide"><span>市场规模计量口径</span><textarea name="market_sizing_basis" rows={3} defaultValue={brief.market_definition.market_sizing_basis} /></label>
            <label className="field fieldWide"><span>竞争者与可比公司识别口径</span><textarea name="competitor_definition" required rows={3} defaultValue={brief.market_definition.competitor_definition} /></label>
            <h3 className="formSectionTitle">研究问题与分析假设</h3>
            <label className="field fieldWide"><span>报告必须回答的问题（每行一项）</span><textarea name="key_questions" required rows={7} defaultValue={brief.key_questions.join("\n")} /></label>
            <div className="fieldGrid">
              <label className="field"><span>当前信息缺口（每行一项）</span><textarea name="information_gaps" required rows={6} defaultValue={brief.information_gaps.join("\n")} /></label>
              <label className="field"><span>待验证假设（每行一项）</span><textarea name="hypotheses" required rows={6} defaultValue={brief.hypotheses.join("\n")} /></label>
            </div>
            {brief.clarification_questions.length > 0 && (
              <div className="clarificationBlock">
                <div className="clarificationIntro"><h3>仍需确认的研究口径</h3><p>左侧是 AI 识别的问题，右侧填写你的确认口径。问题与回答会一并保存。</p></div>
                {brief.clarification_questions.map((question, index) => (
                  <div className="clarificationRow" key={`${index}-${question}`}>
                    <div><span>待确认问题 {index + 1}</span><p>{question}</p></div>
                    <label className="field"><span>研究者确认口径 {index + 1}</span><textarea name={`clarification_response_${index}`} rows={3} defaultValue={brief.clarification_responses[question] || ""} placeholder="在这里输入明确口径；暂不确定时可说明采用的默认假设。" /></label>
                  </div>
                ))}
              </div>
            )}
            <label className="field fieldWide"><span>当前置信度说明</span><textarea name="confidence_note" required rows={3} defaultValue={brief.confidence_note} /></label>
            {message && <div className="formSuccess" role="status">{message}</div>}
            {error && <div className="formError" role="alert">{error}</div>}
            <div className="scopeActions">
              <button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewBrief(form, false); }}>{action === "brief-save" ? "正在保存…" : "保存简报草稿"}</button>
              <button className="primaryButton" type="submit" disabled={action !== null}>{action === "brief-confirm" ? "正在确认…" : "确认研究简报并生成计划"}</button>
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
          <div className="artifactHeading">
            <div>
              <span className="eyebrow">GATE 1 · EVIDENCE REVIEW</span>
              <h2>{evidence.human_confirmed ? "证据矩阵已经确认" : "逐条审核候选证据"}</h2>
              <p>接受表示该陈述可进入后续分析；拒绝表示保留审计记录但不用于形成判断。</p>
            </div>
            <span className={evidence.human_confirmed ? "confirmedLabel" : "reviewRequired"}>{evidence.human_confirmed ? "已确认" : "人工确认 · 必选"}</span>
          </div>
          <form onSubmit={(event) => { event.preventDefault(); void reviewEvidence(event.currentTarget, true); }}>
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
                              <label className="field"><span>审核决定</span><select name={`evidence_status_${item.evidence_id}`} defaultValue={item.review_status === "needs_review" ? "" : item.review_status}><option value="">待决定</option><option value="accepted">接受</option><option value="rejected">拒绝</option></select></label>
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
              <div className="scopeActions">
                <button type="button" className="secondaryButton" disabled={action !== null} onClick={(event) => { const form = event.currentTarget.form; if (form) void reviewEvidence(form, false); }}>{action === "evidence-save" ? "正在保存…" : "保存审核决定"}</button>
                <button type="submit" className="primaryButton" disabled={action !== null}>{action === "evidence-confirm" ? "正在确认…" : "确认 Gate 1 并进入行业分析"}</button>
              </div>
            )}
          </form>
        </section>
      )}
    </main>
  );
}
