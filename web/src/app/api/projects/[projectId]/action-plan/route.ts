import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/action-plan">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/action-plan`, {
    method: "POST",
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/action-plan">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/action-plan`, {
    method: "PATCH",
    body: await request.text(),
  });
}
