import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing`, {
    method: "POST",
    body: await request.text(),
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing`, {
    method: "PATCH",
    body: await request.text(),
  });
}
