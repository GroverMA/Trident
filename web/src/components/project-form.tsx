"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import type { ProjectCreatePayload, ProjectSummary, ResearchPath } from "@/lib/types";

export function ProjectForm({ researchPath }: { researchPath: ResearchPath }) {
  const router = useRouter();
  const [strategyEnabled, setStrategyEnabled] = useState(false);
  const [scenarioPack, setScenarioPack] = useState<"general" | "sme_growth" | "pe_vc">("general");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const payload: ProjectCreatePayload = {
      project_name: String(data.get("project_name") || "").trim(),
      industry: String(data.get("industry") || "").trim(),
      region: String(data.get("region") || "").trim(),
      research_objective: String(data.get("research_objective") || "").trim(),
      time_horizon: String(data.get("time_horizon") || "").trim(),
      output_language: String(data.get("output_language") || "简体中文"),
      company_strategy_enabled: strategyEnabled,
      research_path: researchPath,
      research_mode: "general_research",
      workspace_mode: strategyEnabled ? "analyst_workspace" : "quick_report",
      scenario_pack: scenarioPack,
      scenario_pack_version: "1.0.0",
    };
    if (strategyEnabled) {
      payload.target_company = String(data.get("target_company") || "").trim();
      payload.company_strategy_objective = String(
        data.get("company_strategy_objective") || "",
      ).trim();
    }

    try {
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = (await response.json()) as ProjectSummary & { detail?: unknown };
      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string" ? result.detail : "项目未能创建，请检查必填信息。",
        );
      }
      router.push(`/projects/${result.project_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "项目未能创建，请稍后重试。");
      setSubmitting(false);
    }
  }

  return (
    <section className="projectEntry">
      <div className="sectionHeading">
        <span className="badge badgeAccent">需要填写</span>
        <h2>开始新的行业研究</h2>
        <p>输入本次研究需要回答的问题。适用于任意行业、地区和公司。</p>
      </div>

      <form className="projectForm" onSubmit={submit}>
        <section className="scenarioPicker" aria-labelledby="scenario-heading">
          <div className="subsectionTitle" id="scenario-heading">研究场景</div>
          <p>场景包会改变研究问题、证据重点和交付结构，但始终复用同一套 Trident 研究流程。</p>
          <div className="scenarioOptions">
            {[
              ["general", "通用行业研究", "行业边界、规模、竞争、驱动与未来情景"],
              ["sme_growth", "企业增长决策", "市场机会、能力差距、增长选择与行动计划"],
              ["pe_vc", "PE/VC 赛道研判", "赛道吸引力、投资假设、标的地图与尽调问题"],
            ].map(([id, title, description]) => (
              <button
                className={scenarioPack === id ? "scenarioOption scenarioOptionActive" : "scenarioOption"}
                key={id}
                type="button"
                aria-pressed={scenarioPack === id}
                onClick={() => {
                  const next = id as "general" | "sme_growth" | "pe_vc";
                  setScenarioPack(next);
                  if (next === "sme_growth") setStrategyEnabled(true);
                  if (next !== "sme_growth") setStrategyEnabled(false);
                }}
              >
                <strong>{title}</strong>
                <span>{description}</span>
              </button>
            ))}
          </div>
        </section>

        <section className={strategyEnabled ? "strategyCard strategyCardActive" : "strategyCard"}>
          <div>
            <div className="strategyTitle">企业战略决策支持 · 高级分析模式</div>
            <p>接入企业资料，评估能力与战略适配度，并生成 Company Scorecard 和 Action Plan。</p>
          </div>
          <label className="switchLine">
            <input
              type="checkbox"
              checked={strategyEnabled}
              onChange={(event) => {
                setStrategyEnabled(event.target.checked);
                setScenarioPack(event.target.checked ? "sme_growth" : "general");
              }}
            />
            <span className="switch" aria-hidden="true" />
            <span>进入企业战略决策支持模式</span>
          </label>
        </section>

        <label className="field fieldWide">
          <span>项目名称</span>
          <input name="project_name" required placeholder="例如：全球工业机器人竞争格局研究" />
        </label>
        <div className="fieldGrid">
          <label className="field">
            <span>行业</span>
            <input name="industry" required placeholder="例如：工业机器人" />
          </label>
          <label className="field">
            <span>国家或地区</span>
            <input name="region" required placeholder="例如：全球及中国" />
          </label>
        </div>

        <div className="promptGuide">
          <div className="promptKicker">主要 PROMPT · 必填</div>
          <div className="promptTitle">告诉 AI 这次研究最需要回答什么</div>
          <p>可以写行业现状、竞争格局、市场驱动、商业模式、客户需求、未来趋势，或希望重点验证的假设。</p>
        </div>
        <label className="field fieldWide">
          <span>核心研究目标（必填）</span>
          <textarea
            name="research_objective"
            required
            rows={6}
            placeholder="例如：系统研究全球及中国IVD市场的现状、未来十年的发展状况以及竞争格局。"
          />
        </label>

        {strategyEnabled && (
          <section className="enterpriseFields">
            <div className="subsectionTitle">企业定制基础信息</div>
            <label className="field fieldWide">
              <span>目标企业（必填）</span>
              <input name="target_company" required placeholder="例如：某医疗科技公司（请使用脱敏名称）" />
            </label>
            <label className="field fieldWide">
              <span>企业战略意图（必填）</span>
              <textarea
                name="company_strategy_objective"
                required
                rows={4}
                placeholder="例如：未来三年提高核心医院渗透率，并建立可复制的渠道能力。"
              />
            </label>
          </section>
        )}

        <div className="fieldGrid">
          <label className="field">
            <span>时间范围</span>
            <input name="time_horizon" required placeholder="例如：2026—2036" />
          </label>
          <label className="field">
            <span>输出语言</span>
            <select name="output_language" defaultValue="简体中文">
              <option>简体中文</option>
              <option>English</option>
              <option>中英双语</option>
            </select>
          </label>
        </div>

        {error && <div className="formError" role="alert">{error}</div>}
        <button type="submit" className="primaryButton formSubmit" disabled={submitting}>
          {submitting
            ? "正在创建研究项目…"
            : strategyEnabled
              ? "创建企业战略研究项目"
              : researchPath === "report_review_first"
                ? "创建项目并准备报告初稿"
                : "创建通用研究项目"}
        </button>
      </form>
    </section>
  );
}
