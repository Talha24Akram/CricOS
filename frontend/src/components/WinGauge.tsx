"use client";

import { Pie, PieChart, ResponsiveContainer } from "recharts";

export function WinGauge({ pct }: { pct: number }) {
  const safe = Math.max(0, Math.min(100, pct));
  const data = [
    { name: "win", value: safe, fill: "#00d1b2" },
    { name: "rest", value: 100 - safe, fill: "#22344f" },
  ];

  return (
    <div className="card" style={{ height: 260 }}>
      <h3>Win Probability</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie data={data} dataKey="value" startAngle={180} endAngle={0} innerRadius={60} outerRadius={90} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ marginTop: -30, fontSize: 30, textAlign: "center" }}>{safe.toFixed(1)}%</div>
    </div>
  );
}
