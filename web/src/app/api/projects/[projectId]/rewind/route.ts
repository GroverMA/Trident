import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/rewind">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/rewind`, {
    method: "POST",
    body: "{}",
  });
}
