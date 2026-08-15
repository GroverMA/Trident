"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { ProjectScopePayload, ProjectSummary } from "@/lib/types";

type WorkflowStep = { key: string; label: string; description: string };

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

export function ResearchWorkspace({ initialProject }: { initialProject: ProjectSummary }) {
  const router = useRouter();
  const [project, setProject] = useState(initialProject);
  const [saving, setSaving] = useState<"draft" | "confirm" | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const steps = useMemo(() => stepsFor(project), [project]);

  async function updateScope(form: HTMLFormElement, confirm: boolean) {
    setSaving(confirm ? "confirm" : "draft");
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
      const response = await fetch(`/api/projects/${project.project_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = (await response.json()) as ProjectSummary & { detail?: unknown };
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail : "研究范围未能保存，请检查必填信息。");
      }
      setProject(result);
      setMessage(
        confirm
          ? project.research_path === "report_review_first"
            ? "研究范围已确认。项目已进入报告初稿准备节点，可随时关闭页面后继续。"
            : "研究范围已确认。项目已进入研究规划节点，可随时关闭页面后继续。"
          : "研究范围草稿已保存到云端。",
      );
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "研究范围未能保存，请稍后重试。");
    } finally {
      setSaving(null);
    }
  }

  const completed = steps.filter(
    (step) => project.workflow_status[step.key] === "completed",
  ).length;

  return (
    <main className="workflowCanvas">
      <div className="projectHeading">
        <div>
          <div className="badge badgeAccent">
            {project.research_path === "report_review_first" ? "审阅式研究" : "构建式研究"}
          </div>
          <h1>{project.project_name}</h1>
          <p>{project.research_objective}</p>
        </div>
        <div className="cloudState">
          <span>云端项目</span>
          <strong>{project.market_scope_confirmed_at ? "研究范围已确认" : "研究范围待确认"}</strong>
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
              <div className={`workflowNode workflowNode-${status} ${active ? "workflowNodeActive" : ""}`} key={step.key}>
                <div className="workflowDot">{index + 1}</div>
                <strong>{step.label}</strong>
                <span>{statusLabel(status)}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="scopePanel">
        <div className="scopeIntro">
          <div>
            <span className="eyebrow">SCOPE GATE</span>
            <h2>确认研究目标与市场范围</h2>
            <p>这里决定后续检索、分析和报告使用的统一口径。保存草稿不会推进流程；确认后会进入下一节点。</p>
          </div>
          <div className="scopePathNote">
            <strong>{project.research_path === "report_review_first" ? "自上而下审阅" : "自下而上构建"}</strong>
            <span>{project.research_path === "report_review_first" ? "范围 → 初稿 → 逻辑 → 证据" : "范围 → 规划 → 证据 → 分析 → 报告"}</span>
          </div>
        </div>

        <form onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void updateScope(event.currentTarget, true);
        }}>
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
            <textarea name="research_objective" required rows={7} defaultValue={project.research_objective} />
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
              disabled={saving !== null}
              onClick={(event) => {
                const form = event.currentTarget.form;
                if (form) void updateScope(form, false);
              }}
            >
              {saving === "draft" ? "正在保存…" : "保存范围草稿"}
            </button>
            <button type="submit" className="primaryButton" disabled={saving !== null}>
              {saving === "confirm"
                ? "正在确认…"
                : project.research_path === "report_review_first"
                  ? "确认范围并准备报告初稿"
                  : "确认范围并进入研究规划"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
