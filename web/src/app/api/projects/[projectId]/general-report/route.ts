import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/general-report">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/general-report`, {
    method: "POST",
  });
}
