import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/research-brief">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/research-brief`, {
    method: "POST",
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/research-brief">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/research-brief`, {
    method: "PATCH",
    body: await request.text(),
  });
}
