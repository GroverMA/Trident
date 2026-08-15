"use client";

import type { ResearchPath } from "@/lib/types";

const paths: Array<{
  id: ResearchPath;
  eyebrow: string;
  title: string;
  tag: string;
  copy: string;
  note: string;
  flow: string;
  cta: string;
}> = [
  {
    id: "research_build_first",
    eyebrow: "Research Build First",
    title: "构建式研究",
    tag: "从问题开始，分步骤与 AI 共同完成研究",
    copy: "从研究目标、市场范围和核心问题出发，逐步完成证据收集、分析验证、结论形成与行动建议。",
    note: "适合希望参与研究过程，并在关键节点确认研究方向的用户。",
    flow: "定义问题 → 锁定边界 → 收集证据 → 分析验证 → 形成报告",
    cta: "从问题开始",
  },
  {
    id: "report_review_first",
    eyebrow: "Report Review First",
    title: "审阅式研究",
    tag: "从完整初稿开始审阅，检查和确认您关心的节点",
    copy: "确认研究范围后，由 AI 先完成报告初稿；你可以从结论出发，检查分析逻辑、引用来源、关键假设和决策依据。",
    note: "适合希望快速了解全貌，再针对重点内容深入审阅的用户。",
    flow: "查看结论 → 检查逻辑 → 追溯证据 → 调整判断 → 确认报告",
    cta: "生成报告初稿",
  },
];

export function PathSelector({ onSelect }: { onSelect: (path: ResearchPath) => void }) {
  return (
    <main className="pathPage">
      <div className="pathHero">
        <div className="eyebrow">CHOOSE YOUR RESEARCH PATH</div>
        <h1>选择你的研究方式</h1>
        <p>同一套专业研究标准，两种不同的工作路径。你可以随时切换，已有研究内容不会丢失。</p>
      </div>
      <div className="pathGrid">
        {paths.map((path) => (
          <article className="pathCard" key={path.id}>
            <div className="pathEnglish">{path.eyebrow}</div>
            <h2>{path.title}</h2>
            <div className="pathTag">{path.tag}</div>
            <p className="pathCopy">{path.copy}</p>
            <p className="pathNote"><strong>适合：</strong>{path.note}</p>
            <div className="pathFlow">{path.flow}</div>
            <button type="button" className="primaryButton" onClick={() => onSelect(path.id)}>
              {path.cta}
            </button>
          </article>
        ))}
      </div>
      <p className="pathFootnote">
        两种方式使用相同的研究方法、证据标准与报告结构，区别仅在研究过程的呈现顺序。进入后可随时切换，不会重置研究内容。
      </p>
    </main>
  );
}
