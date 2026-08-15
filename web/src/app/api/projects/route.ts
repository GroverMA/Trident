import { proxyJson } from "@/lib/api";

export async function GET() {
  return proxyJson("/v1/projects");
}

export async function POST(request: Request) {
  return proxyJson("/v1/projects", {
    method: "POST",
    body: await request.text(),
  });
}
