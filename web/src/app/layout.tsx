import type { Metadata } from "next";
import { AgentSidebar } from "@/components/agent-sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trident · Industry Research Intelligence",
  description: "Enterprise research and strategic decision intelligence",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" data-scroll-behavior="smooth">
      <body><div className="agentShell"><AgentSidebar /><div className="agentModule">{children}</div></div></body>
    </html>
  );
}
