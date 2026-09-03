import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing/internal-kpi/feishu/sync">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing/internal-kpi/feishu/sync`, {
    method: "POST",
    body: await request.text(),
  });
}
