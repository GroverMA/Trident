import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/evidence">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/evidence`, {
    method: "POST",
    body: await request.text(),
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/evidence">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/evidence`, {
    method: "PATCH",
    body: await request.text(),
  });
}
