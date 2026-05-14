"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";

export default function TournamentPage() {
  const [teams, setTeams] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    apiGet<Array<{ name: string }>>("/teams")
      .then((res) => setTeams(res.map((x) => x.name)))
      .catch(() => setTeams([]));
  }, []);

  async function runTournament(e: FormEvent) {
    e.preventDefault();
    const payloadTeams = selected.length >= 4 ? selected : teams.slice(0, 4);
    const data = await apiPost("/tournament", {
      teams: payloadTeams,
      venue: "Wankhede Stadium",
      pitch_type: "flat",
      weather_humidity: 0.4,
      dew: false,
    });
    setResult(data);
  }

  return (
    <section className="grid">
      <div className="card">
        <h2 style={{ fontSize: 34 }}>Tournament Simulator</h2>
        <form onSubmit={runTournament}>
          <label>Select teams (Ctrl/Cmd click for multiple)</label>
          <select
            multiple
            style={{ minHeight: 180 }}
            value={selected}
            onChange={(e) => setSelected(Array.from(e.target.selectedOptions).map((opt) => opt.value))}
          >
            {teams.map((team) => (
              <option key={team} value={team}>{team}</option>
            ))}
          </select>
          <button style={{ marginTop: 12 }}>Run Tournament</button>
        </form>
      </div>
      {result && (
        <>
          <div className="card">
            <h3>Standings</h3>
            {result.standings.map((s: any) => (
              <div className="kpi" key={s.team}>{s.team}: {s.points} pts ({s.won}W/{s.lost}L)</div>
            ))}
          </div>
          <div className="card">
            <h3>Fixtures</h3>
            {result.fixtures.map((f: any, idx: number) => (
              <div className="kpi" key={idx}>{f.team1} vs {f.team2} -> {f.winner} ({f.margin})</div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
