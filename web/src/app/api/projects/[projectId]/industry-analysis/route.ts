import { proxyJson } from "@/lib/api";

export async function POST(
  _request: Request,
  context: RouteContext<"/api/projects/[projectId]/industry-analysis">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/industry-analysis`, {
    method: "POST",
  });
}

export async function PATCH(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/industry-analysis">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/industry-analysis`, {
    method: "PATCH",
    body: await request.text(),
  });
}
