"use client";

import { FormEvent, useState } from "react";

import { WinGauge } from "@/components/WinGauge";
import { apiPost } from "@/lib/api";

export default function PredictionPage() {
  const [result, setResult] = useState<any>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const data = await apiPost("/predict", {
      team1: "India",
      team2: "Australia",
      venue: "Wankhede Stadium",
      pitch_type: "flat",
      weather_humidity: 0.4,
      dew: false,
      runs: 1000,
    });
    setResult(data);
  }

  return (
    <section className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
      <div className="card">
        <h2 style={{ fontSize: 34 }}>Prediction Lab</h2>
        <p>Run 1000 simulations and inspect likely outcomes.</p>
        <form onSubmit={submit}>
          <button>Run Prediction</button>
        </form>
        {result && (
          <div className="grid" style={{ marginTop: 12 }}>
            <div className="kpi">Team1 Win %: {result.team1_win_pct}</div>
            <div className="kpi">Team2 Win %: {result.team2_win_pct}</div>
            <div className="kpi">Avg Team1 Score: {result.avg_team1_score}</div>
            <div className="kpi">Avg Team2 Score: {result.avg_team2_score}</div>
          </div>
        )}
      </div>
      <WinGauge pct={Number(result?.team1_win_pct || 0)} />
    </section>
  );
}
