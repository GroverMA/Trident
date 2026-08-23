import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/action-feedback">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/action-feedback`, {
    method: "POST",
    body: await request.text(),
  });
}
