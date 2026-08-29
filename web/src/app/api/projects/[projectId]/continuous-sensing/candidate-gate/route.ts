import { proxyJson } from "@/lib/api";

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/continuous-sensing/candidate-gate">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/continuous-sensing/candidate-gate`, {
    method: "PATCH",
    body: await request.text(),
  });
}
