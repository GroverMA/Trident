import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/research-plan">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/research-plan`, {
    method: "POST",
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/research-plan">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/research-plan`, {
    method: "PATCH",
    body: await request.text(),
  });
}
