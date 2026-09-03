import { proxyJson } from "@/lib/api";

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing/notifications">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing/notifications`, {
    method: "PATCH",
    body: await request.text(),
  });
}
