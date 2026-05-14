"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function ScoreGraph({ points }: { points: Array<{ ball: string; score: number }> }) {
  return (
    <div className="card" style={{ height: 280 }}>
      <h3>Run Progression</h3>
      <ResponsiveContainer width="100%" height="88%">
        <LineChart data={points}>
          <XAxis dataKey="ball" stroke="#8fa2bf" />
          <YAxis stroke="#8fa2bf" />
          <Tooltip />
          <Line dataKey="score" stroke="#00d1b2" dot={false} strokeWidth={2.6} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
