import Link from "next/link";
import { ReportViewer } from "@/components/report-viewer";
import { tridentApiUrl } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";

async function getProject(projectId: string): Promise<ProjectSummary | null> {
  try {
    const response = await fetch(tridentApiUrl(`/v1/projects/${encodeURIComponent(projectId)}`), { cache: "no-store" });
    return response.ok ? await response.json() as ProjectSummary : null;
  } catch { return null; }
}

export default async function GeneralReportPage(props: PageProps<"/projects/[projectId]/report">) {
  const { projectId } = await props.params;
  const project = await getProject(projectId);
  if (!project?.general_report_artifact) return <main className="reportEmpty"><h1>报告尚未生成</h1><p>请先在研究工作台完成报告生成。</p><Link className="primaryButton linkButton" href={`/projects/${projectId}`}>返回研究工作台</Link></main>;
  return <ReportViewer project={project} />;
}
