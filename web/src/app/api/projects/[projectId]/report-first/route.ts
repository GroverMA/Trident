import { proxyJson } from "@/lib/api";

export async function POST(
  request: Request,
  context: RouteContext<"/api/projects/[projectId]/report-first">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/report-first`, {
    method: "POST",
    body: await request.text(),
  });
}
