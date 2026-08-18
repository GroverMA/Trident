import { proxyJson } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyJson("/ready");
}
