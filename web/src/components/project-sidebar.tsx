"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Brand } from "@/components/brand";
import type { ProjectSummary, ResearchPath } from "@/lib/types";

const stages = [
  "research_brief", "research_planning", "evidence_collection", "evidence_qa",
  "industry_analysis", "future_intelligence", "human_review", "decision_report",
];

function progress(project: ProjectSummary) {
  const done = stages.filter((key) => project.workflow_status[key] === "completed").length;
  return Math.round((done / stages.length) * 100);
}

function nodeLabel(project: ProjectSummary) {
  const labels: Record<string, string> = {
    research_brief: "Research Brief",
    research_planning: "Research Planning",
    evidence_collection: "Web Research",
    evidence_qa: "Evidence Review",
    industry_analysis: "Industry Analysis",
    future_intelligence: "Future Intelligence",
    human_review: "Content Review",
    decision_report: "General Report",
  };
  return labels[project.current_step] || "Research Brief";
}

export function ProjectSidebar({
  activeProject,
  researchPath,
}: {
  activeProject?: ProjectSummary;
  researchPath: ResearchPath;
}) {
  const [projects, setProjects] = useState<ProjectSummary[]>(activeProject ? [activeProject] : []);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/projects")
      .then((response) => (response.ok ? response.json() : []))
      .then((items: ProjectSummary[]) => setProjects(items))
      .catch(() => setProjects(activeProject ? [activeProject] : []));
  }, [activeProject]);

  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    if (!query) return projects;
    return projects.filter((item) =>
      `${item.project_name} ${item.industry} ${item.region}`.toLocaleLowerCase().includes(query),
    );
  }, [projects, search]);
  const current = filtered.filter((item) => item.workflow_status.decision_report !== "completed");
  const history = filtered.filter((item) => item.workflow_status.decision_report === "completed");

  const rows = (items: ProjectSummary[], empty: string) => items.length ? items.map((item) => (
    <div className={item.project_id === activeProject?.project_id ? "sidebarProject active" : "sidebarProject"} key={item.project_id}>
      <Link href={`/projects/${item.project_id}`}>
        <strong>{item.project_name}{item.project_id === activeProject?.project_id ? " · 当前" : ""}</strong>
        <span>{item.industry} · {item.region}</span>
        <small>{progress(item)}% · {nodeLabel(item)}</small>
      </Link>
      <button type="button" aria-label={`${item.project_name}项目操作`} title="项目操作">•••</button>
    </div>
  )) : <p className="emptyCopy">{empty}</p>;

  return (
    <aside className="sidebar projectManager">
      <Brand compact />
      <Link className="modeSwitcher" href="/">
        当前研究方式 · {researchPath === "report_review_first" ? "审阅式研究" : "构建式研究"}
        <span>⌄</span>
      </Link>
      <Link className="primaryButton linkButton sidebarButton" href="/">新建研究</Link>
      {activeProject && (
        <div className="sidebarActiveCard">
          <strong>{activeProject.project_name}</strong>
          <span>{activeProject.industry} · {activeProject.region}</span>
          <small>{progress(activeProject)}% · {nodeLabel(activeProject)}</small>
        </div>
      )}
      <input className="sidebarSearch" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索项目" aria-label="搜索研究项目" />
      <section className="sidebarSection">
        <div className="sidebarTitle">进行中的项目</div>
        {rows(current, "暂无进行中的项目")}
      </section>
      <section className="sidebarSection">
        <div className="sidebarTitle">历史研究项目</div>
        {rows(history, "暂无已完成项目")}
      </section>
      <details className="sidebarOrganizer"><summary>项目文件夹与分类</summary><p>项目分类与归档功能将在项目数据模型迁移后启用。</p></details>
      {activeProject && <section className="sidebarWorkspace"><div className="sidebarTitle">当前项目工作台</div><select defaultValue="research"><option value="research">Research Studio · 研究主流程</option></select><details><summary>流程控制</summary><p>可在各人工审核节点返回修改前序内容。</p></details></section>}
      <footer>项目内容保存在云端项目空间。<br />Stage 7B · Strategy-to-Action Studio</footer>
    </aside>
  );
}
