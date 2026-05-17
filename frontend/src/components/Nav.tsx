"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/stats", label: "Stats" },
  { href: "/player/1", label: "Players" },
];

export function Nav() {
  const path = usePathname();

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Link href="/" className="brand">
          <span>🏏</span>
          <span>CricOS</span>
        </Link>
        <nav className="topnav">
          {LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`topnav-link${path === href ? " active" : ""}`}
            >
              {label}
            </Link>
          ))}
        </nav>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 11, color: "var(--muted)", opacity: 0.5 }}>
          AI T20 Sim
        </span>
      </div>
    </header>
  );
}
