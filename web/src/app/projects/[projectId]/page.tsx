import Link from "next/link";
import { Brand } from "@/components/brand";
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
        <main className="projectCanvas">
          <div className="badge badgeAccent">项目已保存至研究服务</div>
          <h1>{project.project_name}</h1>
          <p className="projectLead">{project.research_objective}</p>
          <div className="projectMetrics">
            <div><span>行业与地区</span><strong>{project.industry} · {project.region}</strong></div>
            <div><span>研究路径</span><strong>{project.research_path === "report_review_first" ? "审阅式研究" : "构建式研究"}</strong></div>
            <div><span>当前节点</span><strong>{project.current_step.replaceAll("_", " ")}</strong></div>
          </div>
          <section className="migrationNotice">
            <strong>新的企业级网页底座已经接管项目创建与持久化。</strong>
            <p>下一迁移批次将继续接入市场口径确认、网页研究、证据审核和报告工作台；现有 Streamlit 功能在迁移完成前继续作为兼容版本保留。</p>
          </section>
          <Link className="primaryButton linkButton" href="/">返回项目首页</Link>
        </main>
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
