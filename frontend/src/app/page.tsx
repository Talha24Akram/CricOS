"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiGet, apiPost } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Team = { name: string };
type Venue = { name: string };

const MODE_INFO: Record<string, { label: string; desc: string }> = {
  quicksim:    { label: "QuickSim", desc: "Instant full match result" },
  ai_vs_ai:    { label: "AI vs AI", desc: "Watch two AIs battle it out" },
  user_vs_ai:  { label: "User vs AI", desc: "You control your team ball-by-ball" },
  user_vs_user:{ label: "User vs User", desc: "Two players on one device" },
};

export default function HomePage() {
  const router = useRouter();
  const [teams, setTeams] = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [team1, setTeam1] = useState("India");
  const [team2, setTeam2] = useState("Australia");
  const [venue, setVenue] = useState("Wankhede Stadium");
  const [pitch, setPitch] = useState("flat");
  const [humidity, setHumidity] = useState(0.4);
  const [dew, setDew] = useState(false);
  const [mode, setMode] = useState("ai_vs_ai");

  useEffect(() => {
    apiGet<Team[]>("/teams").then(setTeams).catch(() => setTeams([]));
    apiGet<Venue[]>("/venues").then(setVenues).catch(() => setVenues([]));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "quicksim") {
        // Fast path: immediate simulation → scorecard
        const result = await apiPost("/simulate", {
          team1, team2, venue,
          pitch_type: pitch, weather_humidity: humidity, dew, mode,
        });
        localStorage.setItem("cricketos:lastSimulation", JSON.stringify(result));
        router.push("/live");
        return;
      }

      // Interactive path: create session → setup (user_vs_ai / user_vs_user) or toss (ai_vs_ai)
      const res = await fetch(`${API}/game/new`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode, team1, team2, venue,
          pitch_type: pitch, weather_humidity: humidity, dew,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const session = await res.json();
      const sid = session.session_id;

      if (mode === "user_vs_ai" || mode === "user_vs_user") {
        router.push(`/setup?session=${sid}&team1=${encodeURIComponent(team1)}&team2=${encodeURIComponent(team2)}&mode=${mode}`);
      } else {
        // ai_vs_ai: lineups auto-set, go straight to toss
        router.push(`/toss?session=${sid}&team1=${encodeURIComponent(team1)}&team2=${encodeURIComponent(team2)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start match");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid" style={{ gridTemplateColumns: "1.2fr 1fr" }}>
      <form className="card grid" onSubmit={onSubmit}>
        <h2 style={{ fontSize: 32 }}>Start A Match</h2>
        <div>
          <label>Team 1</label>
          <select value={team1} onChange={(e) => setTeam1(e.target.value)}>
            {(teams.length ? teams : [{ name: "India" }, { name: "Australia" }]).map((t) => (
              <option key={t.name}>{t.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Team 2</label>
          <select value={team2} onChange={(e) => setTeam2(e.target.value)}>
            {(teams.length ? teams : [{ name: "India" }, { name: "Australia" }]).map((t) => (
              <option key={t.name}>{t.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Venue</label>
          <select value={venue} onChange={(e) => setVenue(e.target.value)}>
            {(venues.length ? venues : [{ name: "Wankhede Stadium" }]).map((v) => (
              <option key={v.name}>{v.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Pitch Type</label>
          <select value={pitch} onChange={(e) => setPitch(e.target.value)}>
            <option value="green">Green</option>
            <option value="flat">Flat</option>
            <option value="dusty">Dusty</option>
            <option value="slow">Slow</option>
            <option value="worn">Worn</option>
          </select>
        </div>
        <div>
          <label>Humidity ({humidity.toFixed(2)})</label>
          <input
            type="range" min={0} max={1} step={0.01}
            value={humidity} onChange={(e) => setHumidity(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Mode</label>
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            {Object.entries(MODE_INFO).map(([k, v]) => (
              <option key={k} value={k}>{v.label} — {v.desc}</option>
            ))}
          </select>
        </div>
        <div>
          <label>
            <input type="checkbox" checked={dew} onChange={(e) => setDew(e.target.checked)} /> Dew in 2nd innings
          </label>
        </div>
        <button disabled={loading}>
          {loading ? "Loading..." : mode === "quicksim" ? "Simulate" : "Start Match →"}
        </button>
        {error && <p style={{ color: "#ff7878" }}>{error}</p>}
      </form>

      <article className="card">
        <h2 style={{ fontSize: 32 }}>CricOS</h2>
        <p>AI-powered T20 cricket sim with phase-aware tactics, batting mindsets, field placement, and live ball-by-ball play.</p>
        <div className="kpis">
          <div className="kpi">
            <div className="small">Modes</div>
            <strong>4</strong>
          </div>
          <div className="kpi">
            <div className="small">Phase Engine</div>
            <strong>PP / MID / DEATH</strong>
          </div>
          <div className="kpi">
            <div className="small">Monte Carlo</div>
            <strong>1000 Runs</strong>
          </div>
          <div className="kpi">
            <div className="small">Commentary</div>
            <strong>3 Tones</strong>
          </div>
        </div>
      </article>
    </section>
  );
}
