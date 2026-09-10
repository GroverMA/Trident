import { proxyJson } from "@/lib/api";

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/metadata">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/metadata`, {
    method: "PATCH",
    body: await request.text(),
  });
}
