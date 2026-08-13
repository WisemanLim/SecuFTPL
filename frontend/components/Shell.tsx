"use client";
// 좌측 접이식 사이드바 셸 (PRD §7.11)
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/", ico: "▦", label: "대시보드" },
  { href: "/pipeline", ico: "➤", label: "파이프라인" },
  { sep: true },
  { href: "/models", ico: "◆", label: "모델" },
  { href: "/datasets", ico: "▤", label: "데이터셋" },
  { href: "/queue", ico: "✓", label: "검수 큐" },
  { href: "/tuning", ico: "⚙", label: "튜닝" },
  { href: "/leaderboard", ico: "▲", label: "리더보드" },
] as const;

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  useEffect(() => {
    setCollapsed(localStorage.getItem("secuftpl.sidebar") === "collapsed");
  }, []);
  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("secuftpl.sidebar", next ? "collapsed" : "open");
  };

  return (
    <div className="shell">
      <aside className={"sidebar" + (collapsed ? " collapsed" : "")}>
        <div className="brand">
          <button className="toggle" onClick={toggle}
                  aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}>
            {collapsed ? "»" : "«"}
          </button>
          {!collapsed && <b>SecuFTPL</b>}
        </div>
        {NAV.map((item, i) =>
          "sep" in item ? (
            <div key={`sep-${i}`} className="sep" />
          ) : (
            <Link key={item.href} href={item.href} title={item.label}
                  className={"nav" + (pathname === item.href ? " active" : "")}>
              <span className="ico" aria-hidden>{item.ico}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          ),
        )}
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
