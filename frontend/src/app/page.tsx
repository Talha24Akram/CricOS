"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiGet, apiPost } from "@/lib/api";

type Team = { name: string };
type Venue = { name: string };

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
      const result = await apiPost("/simulate", {
        team1,
        team2,
        venue,
        pitch_type: pitch,
        weather_humidity: humidity,
        dew,
        mode,
      });
      localStorage.setItem("cricketos:lastSimulation", JSON.stringify(result));
      router.push("/live");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
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
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={humidity}
            onChange={(e) => setHumidity(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Mode</label>
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="ai_vs_ai">AI vs AI</option>
            <option value="user_vs_ai">User vs AI</option>
            <option value="user_vs_user">User vs User</option>
            <option value="quicksim">QuickSim</option>
          </select>
        </div>
        <div>
          <label>
            <input type="checkbox" checked={dew} onChange={(e) => setDew(e.target.checked)} /> Dew in 2nd innings
          </label>
        </div>
        <button disabled={loading}>{loading ? "Simulating..." : "Simulate"}</button>
        {error && <p style={{ color: "#ff7878" }}>{error}</p>}
      </form>

      <article className="card">
        <h2 style={{ fontSize: 32 }}>What You Can Do</h2>
        <p>Run alternate cricket timelines with tactics, pressure, and momentum swings baked into each ball outcome.</p>
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
            <strong>Claude Sonnet</strong>
          </div>
        </div>
      </article>
    </section>
  );
}
