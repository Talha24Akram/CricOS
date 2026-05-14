"use client";

import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

export function RadarRatings({ ratings }: { ratings: Record<string, number> }) {
  const keys = ["power", "timing", "pace_handling", "spin_handling", "aggression", "clutch"];
  const data = keys.map((k) => ({ metric: k, value: ratings[k] || 50 }));

  return (
    <div className="card" style={{ height: 320 }}>
      <h3>Ratings Radar</h3>
      <ResponsiveContainer width="100%" height="88%">
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" />
          <Radar dataKey="value" stroke="#ff6b35" fill="#ff6b35" fillOpacity={0.35} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
