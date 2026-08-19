"use client";

import Link from "next/link";
import { Fragment, ReactNode, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import type { ProjectSummary } from "@/lib/types";

type FontChoice = "sans" | "serif" | "system";
type PageWidth = "focused" | "standard" | "wide";

const FONT_FAMILIES: Record<FontChoice, string> = {
  sans: "Inter, 'Noto Sans CJK SC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
  serif: "'Noto Serif CJK SC', 'Songti SC', SimSun, serif",
  system: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif",
};

function inlineMarkdown(value: string): ReactNode[] {
  const pattern = /(\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`)/g;
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(value)) !== null) {
    if (match.index > cursor) nodes.push(value.slice(cursor, match.index));
    if (match[2] && match[3]) nodes.push(<a key={`${match.index}-a`} href={match[3]} target="_blank" rel="noreferrer">{match[2]}</a>);
    else if (match[4]) nodes.push(<strong key={`${match.index}-b`}>{match[4]}</strong>);
    else if (match[5]) nodes.push(<code key={`${match.index}-c`}>{match[5]}</code>);
    cursor = pattern.lastIndex;
  }
  if (cursor < value.length) nodes.push(value.slice(cursor));
  return nodes;
}

function MarkdownReport({ markdown, title }: { markdown: string; title: string }) {
  const rawLines = markdown.replace(/\r\n/g, "\n").split("\n");
  const firstContent = rawLines.findIndex((line) => line.trim());
  const firstHeading = firstContent >= 0 ? /^#\s+(.+)$/.exec(rawLines[firstContent].trim()) : null;
  const lines = firstHeading?.[1].trim() === title.trim()
    ? rawLines.filter((_line, index) => index !== firstContent)
    : rawLines;
  const output: ReactNode[] = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index].trimEnd();
    if (!line.trim()) { index += 1; continue; }
    const heading = /^(#{1,4})\s+(.+)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const content = inlineMarkdown(heading[2]);
      output.push(level === 1 ? <h1 key={index}>{content}</h1> : level === 2 ? <h2 key={index}>{content}</h2> : level === 3 ? <h3 key={index}>{content}</h3> : <h4 key={index}>{content}</h4>);
      index += 1; continue;
    }
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) items.push(lines[index++].trim().replace(/^[-*]\s+/, ""));
      output.push(<ul key={`ul-${index}`}>{items.map((item, itemIndex) => <li key={itemIndex}>{inlineMarkdown(item)}</li>)}</ul>);
      continue;
    }
    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\d+[.)]\s+/.test(lines[index].trim())) items.push(lines[index++].trim().replace(/^\d+[.)]\s+/, ""));
      output.push(<ol key={`ol-${index}`}>{items.map((item, itemIndex) => <li key={itemIndex}>{inlineMarkdown(item)}</li>)}</ol>);
      continue;
    }
    if (line.includes("|") && index + 1 < lines.length && /^\s*\|?\s*:?-+/.test(lines[index + 1])) {
      const cells = (row: string) => row.replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
      const headers = cells(line); index += 2;
      const rows: string[][] = [];
      while (index < lines.length && lines[index].includes("|")) rows.push(cells(lines[index++]));
      output.push(<div className="reportTableWrap" key={`table-${index}`}><table><thead><tr>{headers.map((cell, cellIndex) => <th key={cellIndex}>{inlineMarkdown(cell)}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{inlineMarkdown(cell)}</td>)}</tr>)}</tbody></table></div>);
      continue;
    }
    const paragraph: string[] = [line.trim()]; index += 1;
    while (index < lines.length && lines[index].trim() && !/^(#{1,4})\s+|^[-*]\s+|^\d+[.)]\s+/.test(lines[index].trim())) paragraph.push(lines[index++].trim());
    output.push(<p key={`p-${index}`}>{inlineMarkdown(paragraph.join(" "))}</p>);
  }
  return <>{output.map((node, nodeIndex) => <Fragment key={nodeIndex}>{node}</Fragment>)}</>;
}

export function ReportViewer({ project }: { project: ProjectSummary }) {
  const report = project.general_report_artifact!;
  const storageKey = `trident-report-style-${project.project_id}`;
  const [font, setFont] = useState<FontChoice>("sans");
  const [headingColor, setHeadingColor] = useState("#172033");
  const [bodyColor, setBodyColor] = useState("#3f4a5e");
  const [bodySize, setBodySize] = useState(16);
  const [titleSize, setTitleSize] = useState(34);
  const [lineHeight, setLineHeight] = useState(1.85);
  const [pageWidth, setPageWidth] = useState<PageWidth>("standard");
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    let active = true;
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (!saved) return;
      queueMicrotask(() => {
        if (!active) return;
        if (saved.font) setFont(saved.font);
        if (saved.headingColor) setHeadingColor(saved.headingColor);
        if (saved.bodyColor) setBodyColor(saved.bodyColor);
        if (saved.bodySize) setBodySize(saved.bodySize);
        if (saved.titleSize) setTitleSize(saved.titleSize);
        if (saved.lineHeight) setLineHeight(saved.lineHeight);
        if (saved.pageWidth) setPageWidth(saved.pageWidth);
      });
    } catch { /* keep accessible defaults */ }
    return () => { active = false; };
  }, [storageKey]);

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify({ font, headingColor, bodyColor, bodySize, titleSize, lineHeight, pageWidth }));
  }, [storageKey, font, headingColor, bodyColor, bodySize, titleSize, lineHeight, pageWidth]);

  const style = useMemo(() => ({
    "--report-font": FONT_FAMILIES[font], "--report-heading": headingColor, "--report-body": bodyColor,
    "--report-body-size": `${bodySize}px`, "--report-title-size": `${titleSize}px`, "--report-line-height": lineHeight,
  }) as CSSProperties, [font, headingColor, bodyColor, bodySize, titleSize, lineHeight]);

  return <main className="reportPage">
    <header className="reportTopbar">
      <Link href={`/projects/${project.project_id}`} className="reportBack">← 返回研究工作台</Link>
      <div className="reportTopActions"><span className="reportStatus">报告已生成</span><button type="button" className="secondaryButton" onClick={() => setSettingsOpen((value) => !value)} aria-expanded={settingsOpen}>显示设置</button><button type="button" className="secondaryButton" onClick={() => window.print()}>打印 / 保存 PDF</button></div>
    </header>
    {settingsOpen && <section className="reportSettings" aria-label="报告显示设置">
      <div className="reportSettingsIntro"><strong>报告显示设置</strong><span>设置只影响当前浏览器的阅读呈现，不修改研究内容。</span></div>
      <label><span>字体</span><select value={font} onChange={(event) => setFont(event.target.value as FontChoice)}><option value="sans">专业无衬线</option><option value="serif">报告宋体</option><option value="system">系统字体</option></select></label>
      <label><span>报告标题</span><input type="range" min="28" max="48" value={titleSize} onChange={(event) => setTitleSize(Number(event.target.value))} /><b>{titleSize}px</b></label>
      <label><span>正文</span><input type="range" min="14" max="21" value={bodySize} onChange={(event) => setBodySize(Number(event.target.value))} /><b>{bodySize}px</b></label>
      <label><span>行距</span><input type="range" min="1.4" max="2.2" step="0.05" value={lineHeight} onChange={(event) => setLineHeight(Number(event.target.value))} /><b>{lineHeight}</b></label>
      <label><span>标题颜色</span><input type="color" value={headingColor} onChange={(event) => setHeadingColor(event.target.value)} /></label>
      <label><span>正文颜色</span><input type="color" value={bodyColor} onChange={(event) => setBodyColor(event.target.value)} /></label>
      <label><span>页面宽度</span><select value={pageWidth} onChange={(event) => setPageWidth(event.target.value as PageWidth)}><option value="focused">专注</option><option value="standard">标准</option><option value="wide">宽屏</option></select></label>
    </section>}
    <article className={`reportDocument reportWidth-${pageWidth}`} style={style}>
      <div className="reportMasthead"><span>GENERAL REPORT</span><h1>{report.title}</h1><p>{report.source_count} 个来源 · {report.accepted_finding_ids.length} 项行业判断 · {report.accepted_trend_ids.length} 项趋势 · {new Date(report.generated_at).toLocaleDateString("zh-CN")}</p></div>
      {report.unresolved_prompt_questions.length > 0 && <aside className="reportUnresolved"><h2>仍未完全回答的问题</h2><ul>{report.unresolved_prompt_questions.map((item) => <li key={item}>{item}</li>)}</ul></aside>}
      <div className="reportContent"><MarkdownReport markdown={report.markdown} title={report.title} /></div>
    </article>
  </main>;
}
