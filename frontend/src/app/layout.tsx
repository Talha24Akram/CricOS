import "./globals.css";
import type { ReactNode } from "react";

import { Nav } from "@/components/Nav";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="shell">
          <h1 style={{ fontSize: 52, color: "#00d1b2" }}>CricketOS</h1>
          <p className="small">AI-powered T20 simulation sandbox</p>
          <Nav />
          {children}
        </main>
      </body>
    </html>
  );
}
