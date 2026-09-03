import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing/internal-kpi">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing/internal-kpi`, {
    method: "POST",
    body: await request.text(),
  });
}
