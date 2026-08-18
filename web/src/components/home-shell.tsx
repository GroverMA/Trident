"use client";

import { useEffect, useState } from "react";
import { PathSelector } from "@/components/path-selector";
import { ProjectForm } from "@/components/project-form";
import { ProjectSidebar } from "@/components/project-sidebar";
import type { ResearchPath } from "@/lib/types";

export function HomeShell() {
  const [researchPath, setResearchPath] = useState<ResearchPath | null>(null);
  useEffect(() => { window.scrollTo(0, 0); }, [researchPath]);

  if (!researchPath) {
    return <PathSelector onSelect={setResearchPath} />;
  }

  return (
    <div className="appShell">
      <ProjectSidebar researchPath={researchPath} />

      <main className="workspace">
        <section className="hero">
          <div className="eyebrow">ENTERPRISE INDUSTRY RESEARCH &amp; STRATEGIC DECISION-MAKING AGENT</div>
          <div className="heroLockup">
            <h1>Trident</h1>
            <div className="heroSlogan">Dive Deep into Industries.<br />Surface with Direction.</div>
          </div>
          <p>你的专属 AI 行业分析师：洞察未来趋势与竞争格局，发现市场机会，找到增长路径。</p>
        </section>

        <div className="homeGrid">
          <ProjectForm researchPath={researchPath} />
          <aside className="infoColumn">
            <div className="sectionHeading">
              <span className="badge">仅供浏览</span>
              <h2>产品介绍与案例</h2>
              <p>了解产品能力与可拓展方向，此区域无需填写。</p>
            </div>
            <section className="infoCard">
              <h3>案例展示 · 中国 IVD 行业</h3>
              <div className="infoMeta">Industry Pack Enabled · 高精度研究案例</div>
              <p>展示从市场口径、网页证据、趋势预测到企业决策建议的完整研究深度。</p>
              <button className="secondaryButton" type="button">案例将在下一迁移批次接入</button>
            </section>
            <section className="infoCard">
              <h3>产品优势</h3>
              {[
                ["通用行业底座", "任意行业均可研究，并可接入行业知识包。"],
                ["证据优先", "重要结论连接原始来源，识别冲突与证据边界。"],
                ["人工审核", "市场口径、证据与报告内容均由用户确认。"],
                ["决策输出", "行业洞察进一步映射至公司评分与行动计划。"],
              ].map(([title, copy]) => (
                <div className="advantage" key={title}>
                  <strong>{title}</strong>
                  <span>{copy}</span>
                </div>
              ))}
            </section>
          </aside>
        </div>
      </main>
    </div>
  );
}
