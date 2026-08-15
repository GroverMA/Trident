const DEFAULT_API_URL = "http://127.0.0.1:8000";

export function tridentApiUrl(path: string): string {
  const baseUrl = (process.env.TRIDENT_API_URL || DEFAULT_API_URL).replace(/\/$/, "");
  return `${baseUrl}${path}`;
}

export async function proxyJson(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  try {
    const upstream = await fetch(tridentApiUrl(path), {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
    });
  } catch {
    return Response.json(
      {
        detail:
          "研究服务暂时无法连接。请确认 FastAPI 已启动，或在部署环境配置 TRIDENT_API_URL。",
      },
      { status: 503 },
    );
  }
}
