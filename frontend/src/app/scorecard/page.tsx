"use client";

import { useEffect, useState } from "react";

export default function ScorecardPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const raw = localStorage.getItem("cricketos:lastSimulation");
    if (raw) setData(JSON.parse(raw));
  }, []);

  if (!data) return <div className="card">Run a match to see scorecards.</div>;

  return (
    <section className="grid">
      <h2 style={{ fontSize: 34 }}>Scorecard</h2>
      {data.innings.map((inn: any, idx: number) => (
        <article className="card" key={idx}>
          <h3>{inn.team} - {inn.runs}/{inn.wickets}</h3>
          <p className="small">Balls: {inn.balls}</p>
          <div className="grid">
            {inn.over_summary.map((line: string, i: number) => (
              <div key={i} className="kpi">{line}</div>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
