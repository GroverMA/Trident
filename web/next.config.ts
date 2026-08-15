import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel packages the Next.js runtime itself. Standalone output remains
  // available for the Docker deployment path, but must not be enabled during
  // Vercel builds because it conflicts with Vercel's output-file tracing.
  output: process.env.VERCEL ? undefined : "standalone",
  typedRoutes: true,
};

export default nextConfig;
