import { proxyJson } from "@/lib/api";

export async function GET(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}`);
}
