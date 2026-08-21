"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Brand } from "@/components/brand";

const items = [
  { href: "/projects", label: "项目管理", note: "跨场景保存、切换与继续" },
  { href: "/knowledge", label: "企业知识库", note: "画像、经营、决策与反馈" },
  { href: "/sensing", label: "持续感知", note: "新闻、政策与经营变化" },
  { href: "/feedback", label: "决策与行动质量", note: "跨项目反馈与调整 Dashboard" },
  { href: "/ops", label: "运营监测", note: "Token、耗时与完成情况" },
  { href: "/research#knowledge", label: "研究方法库", note: "Skill、证据与方法资产" },
];

export function AgentSidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return <>
    <button className="agentMobileNav" type="button" onClick={() => setOpen(true)} aria-expanded={open}>功能导航</button>
    {open && <button className="agentNavBackdrop" type="button" aria-label="关闭导航" onClick={() => setOpen(false)} />}
    <aside className={`agentSidebar ${open ? "agentSidebarOpen" : ""}`}>
      <div className="agentMobileHead"><strong>Trident Agent</strong><button type="button" onClick={() => setOpen(false)}>关闭</button></div>
      <Brand compact />
      <p className="agentSidebarIntro">场景决定工作流；知识、信号与行动反馈跨场景持续积累。</p>
      <nav className="agentNav" aria-label="Agent 功能">
        <Link href="/" className={pathname === "/" ? "agentNavItem active" : "agentNavItem"} onClick={() => setOpen(false)}><span>01</span><div><strong>场景选择</strong><small>行业研究 / PE / VC / 企业增长</small></div></Link>
        {items.map((item, index) => <Link key={item.label} href={item.href as "/"} className={(!item.href.includes("#") && pathname.startsWith(item.href)) ? "agentNavItem active" : "agentNavItem"} onClick={() => setOpen(false)}>
          <span>{String(index + 2).padStart(2, "0")}</span><div><strong>{item.label}</strong><small>{item.note}</small></div>
        </Link>)}
      </nav>
      <section className="agentComing"><span>统一资产层</span><strong>一个企业，一套长期记忆</strong><p>不同场景产生的画像、证据、判断、行动和反馈都进入同一企业知识库，并保留来源与版本。</p></section>
      <footer><span>TRIDENT DECISION INTELLIGENCE</span><small>同一研究内核 · 多场景决策工作流</small></footer>
    </aside>
  </>;
}
