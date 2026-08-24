import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/plan-revision">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/plan-revision`, {
    method: "POST",
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/plan-revision">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/plan-revision`, {
    method: "PATCH",
    body: await request.text(),
  });
}
