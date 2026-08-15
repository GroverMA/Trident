"use client";

import { useEffect, useState } from "react";
import { Brand } from "@/components/brand";
import { PathSelector } from "@/components/path-selector";
import { ProjectForm } from "@/components/project-form";
import type { ProjectSummary, ResearchPath } from "@/lib/types";

export function HomeShell() {
  const [researchPath, setResearchPath] = useState<ResearchPath | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    fetch("/api/projects")
      .then((response) => (response.ok ? response.json() : []))
      .then((items: ProjectSummary[]) => setProjects(items.slice(0, 5)))
      .catch(() => setProjects([]));
  }, []);

  return (
    <>
      {!researchPath && <PathSelector onSelect={setResearchPath} />}
      <div
        aria-hidden={!researchPath}
        className={researchPath ? "appShell" : "appShell appShellHidden"}
      >
      <aside className="sidebar">
        <Brand compact />
        <button className="primaryButton sidebarButton" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
          新建研究
        </button>
        <button className="pathSwitch" onClick={() => setResearchPath(null)}>
          <span>当前研究方式</span>
          <strong>{researchPath === "report_review_first" ? "审阅式研究" : "构建式研究"}</strong>
          <small>点击切换，不会清空项目</small>
        </button>
        <div className="sidebarSection">
          <div className="sidebarTitle">最近项目</div>
          {projects.length ? (
            projects.map((project) => (
              <a className="projectRow" href={`/projects/${project.project_id}`} key={project.project_id}>
                <strong>{project.project_name}</strong>
                <span>{project.industry} · {project.region}</span>
              </a>
            ))
          ) : (
            <p className="emptyCopy">创建后的研究项目会显示在这里。</p>
          )}
        </div>
      </aside>

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
          <ProjectForm researchPath={researchPath ?? "research_build_first"} />
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
    </>
  );
}
