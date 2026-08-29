import { proxyJson } from "@/lib/api";

export async function PUT(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing/subscription">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing/subscription`, {
    method: "PUT",
    body: await request.text(),
  });
}
