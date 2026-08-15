import Link from "next/link";
import { Brand } from "@/components/brand";
import { ResearchWorkspace } from "@/components/research-workspace";
import { tridentApiUrl } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";

async function getProject(projectId: string): Promise<ProjectSummary | null> {
  try {
    const response = await fetch(tridentApiUrl(`/v1/projects/${encodeURIComponent(projectId)}`), {
      cache: "no-store",
    });
    return response.ok ? ((await response.json()) as ProjectSummary) : null;
  } catch {
    return null;
  }
}

export default async function ProjectPage(
  props: PageProps<"/projects/[projectId]">,
) {
  const { projectId } = await props.params;
  const project = await getProject(projectId);

  return (
    <div className="projectPage">
      <header className="projectTopbar">
        <Brand compact />
        <Link className="secondaryButton linkButton" href="/">新建研究</Link>
      </header>
      {project ? (
        <ResearchWorkspace initialProject={project} />
      ) : (
        <main className="projectCanvas">
          <h1>暂时无法读取这个项目</h1>
          <p className="projectLead">请确认研究服务正在运行，然后重新打开项目。</p>
          <Link className="primaryButton linkButton" href="/">返回首页</Link>
        </main>
      )}
    </div>
  );
}
