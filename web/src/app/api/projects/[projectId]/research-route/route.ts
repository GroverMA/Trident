import { proxyJson } from "@/lib/api";

type RouteContext<T extends string> = { params: Promise<Record<T, string>> };

export async function POST(
  request: Request,
  context: RouteContext<"projectId">,
) {
  const { projectId } = await context.params;
  return proxyJson(`/v1/projects/${encodeURIComponent(projectId)}/research-route`, {
    method: "POST",
    body: await request.text(),
  });
}
