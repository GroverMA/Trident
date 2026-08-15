import { proxyJson } from "@/lib/api";

export async function GET(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}`);
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]">,
) {
  const { projectId } = await context.params;
  const body = await request.text();
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/scope`, {
    method: "PATCH",
    body,
  });
}
