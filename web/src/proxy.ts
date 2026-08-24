import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const username = process.env.TRIDENT_OPS_USERNAME;
  const password = process.env.TRIDENT_OPS_PASSWORD;
  if (!username || !password) {
    // Let the page render its safe configuration diagnostic. The telemetry
    // request still requires the server-only operations key, so no private
    // monitoring data is exposed when access control is incomplete.
    return NextResponse.next();
  }

  const authorization = request.headers.get("authorization");
  if (authorization?.startsWith("Basic ")) {
    try {
      const decoded = atob(authorization.slice(6));
      const separator = decoded.indexOf(":");
      if (
        separator >= 0 &&
        decoded.slice(0, separator) === username &&
        decoded.slice(separator + 1) === password
      ) {
        return NextResponse.next();
      }
    } catch {
      // Fall through to the browser's secure Basic Auth challenge.
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Trident Operations"' },
  });
}

export const config = { matcher: "/ops/:path*" };
