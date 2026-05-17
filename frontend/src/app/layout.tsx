import "./globals.css";
import type { ReactNode } from "react";
import { Nav } from "@/components/Nav";

export const metadata = {
  title: "CricOS — AI T20 Cricket Simulator",
  description: "Phase-aware T20 cricket simulation with interactive batting, bowling, and tactical AI",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="shell">
          {children}
        </main>
      </body>
    </html>
  );
}
