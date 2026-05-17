"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type Team  = { name: string };
type Venue = { name: string };

const MODES = [
  {
    key: "quicksim",
    icon: "⚡",
    label: "Quick Sim",
    desc: "Instant full-match result",
    color: "#f59e0b",
  },
  {
    key: "ai_vs_ai",
    icon: "🤖",
    label: "AI vs AI",
    desc: "Watch two AIs battle it out",
    color: "#8b5cf6",
  },
  {
    key: "user_vs_ai",
    icon: "🕹️",
    label: "User vs AI",
    desc: "You control your team, ball by ball",
    color: "#00d1b2",
  },
  {
    key: "user_vs_user",
    icon: "👥",
    label: "User vs User",
    desc: "Two players on one device",
    color: "#ff6b35",
  },
] as const;

const PITCH_TYPES = [
  { key: "flat",   label: "Flat",   desc: "High-scoring, good for batters" },
  { key: "green",  label: "Green",  desc: "Seam movement, helps pacers" },
  { key: "dusty",  label: "Dusty",  desc: "Turn on offer for spinners" },
  { key: "slow",   label: "Slow",   desc: "Variable bounce, tricky" },
  { key: "worn",   label: "Worn",   desc: "Deteriorating, unpredictable" },
];

export default function HomePage() {
  const router = useRouter();
  const [teams,  setTeams]  = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const [team1,    setTeam1]    = useState("India");
  const [team2,    setTeam2]    = useState("Australia");
  const [venue,    setVenue]    = useState("Wankhede Stadium");
  const [pitch,    setPitch]    = useState("flat");
  const [humidity, setHumidity] = useState(0.4);
  const [dew,      setDew]      = useState(false);
  const [mode,     setMode]     = useState("ai_vs_ai");
  const [advanced, setAdvanced] = useState(false);

  useEffect(() => {
    apiGet<Team[]>("/teams").then(setTeams).catch(() => setTeams([]));
    apiGet<Venue[]>("/venues").then(setVenues).catch(() => setVenues([]));
  }, []);

  const teamList  = teams.length  ? teams  : [{ name: "India" }, { name: "Australia" }];
  const venueList = venues.length ? venues : [{ name: "Wankhede Stadium" }];

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (team1 === team2) { setError("Pick two different teams."); return; }
    setLoading(true);
    setError("");
    try {
      if (mode === "quicksim") {
        const result = await apiPost("/simulate", {
          team1, team2, venue, pitch_type: pitch, weather_humidity: humidity, dew, mode,
        });
        localStorage.setItem("cricketos:lastSimulation", JSON.stringify(result));
        router.push("/live");
        return;
      }
      const res = await fetch(`${API}/game/new`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, team1, team2, venue, pitch_type: pitch, weather_humidity: humidity, dew }),
      });
      if (!res.ok) throw new Error(await res.text());
      const session = await res.json();
      const sid = session.session_id;
      if (mode === "user_vs_ai" || mode === "user_vs_user") {
        router.push(`/setup?session=${sid}&team1=${encodeURIComponent(team1)}&team2=${encodeURIComponent(team2)}&mode=${mode}`);
      } else {
        router.push(`/toss?session=${sid}&team1=${encodeURIComponent(team1)}&team2=${encodeURIComponent(team2)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start match");
    } finally {
      setLoading(false);
    }
  }

  const selectedMode = MODES.find((m) => m.key === mode)!;

  return (
    <div style={{ maxWidth: 860, margin: "0 auto" }}>
      {/* Hero */}
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <h1 style={{ fontSize: 52, color: "var(--accent)", marginBottom: 8 }}>
          CricOS
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 15, maxWidth: 420, margin: "0 auto" }}>
          AI-powered T20 cricket with phase tactics, batting mindsets, field placement, and live ball-by-ball play
        </p>
      </div>

      <form onSubmit={onSubmit}>
        {/* Mode selection */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 12 }}>
            Select Mode
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {MODES.map((m) => (
              <button
                key={m.key}
                type="button"
                onClick={() => setMode(m.key)}
                style={{
                  width: "100%",
                  padding: "14px 12px",
                  borderRadius: 12,
                  border: `2px solid ${mode === m.key ? m.color : "var(--line)"}`,
                  background: mode === m.key ? `${m.color}18` : "rgba(9,13,20,0.6)",
                  color: mode === m.key ? m.color : "var(--muted)",
                  cursor: "pointer",
                  textAlign: "center",
                  transition: "all 0.15s",
                  transform: "none",
                }}
              >
                <div style={{ fontSize: 26, marginBottom: 6 }}>{m.icon}</div>
                <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4, color: mode === m.key ? m.color : "var(--ink)" }}>{m.label}</div>
                <div style={{ fontSize: 10, opacity: 0.7, lineHeight: 1.3 }}>{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Teams */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 12, alignItems: "end" }}>
            <div>
              <label>Team 1 {(mode === "user_vs_ai" || mode === "user_vs_user") && <span style={{ color: "var(--accent)", fontWeight: 700 }}>(You)</span>}</label>
              <select value={team1} onChange={(e) => setTeam1(e.target.value)}>
                {teamList.map((t) => <option key={t.name}>{t.name}</option>)}
              </select>
            </div>
            <div style={{ paddingBottom: 2, color: "var(--muted)", fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, letterSpacing: 2 }}>VS</div>
            <div>
              <label>Team 2</label>
              <select value={team2} onChange={(e) => setTeam2(e.target.value)}>
                {teamList.map((t) => <option key={t.name}>{t.name}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Venue */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <label>Venue</label>
              <select value={venue} onChange={(e) => setVenue(e.target.value)}>
                {venueList.map((v) => <option key={v.name}>{v.name}</option>)}
              </select>
            </div>
            <div>
              <label>Pitch Type</label>
              <select value={pitch} onChange={(e) => setPitch(e.target.value)}>
                {PITCH_TYPES.map((p) => (
                  <option key={p.key} value={p.key}>{p.label} — {p.desc}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Advanced conditions toggle */}
          <button
            type="button"
            onClick={() => setAdvanced((v) => !v)}
            style={{
              width: "auto",
              background: "none",
              border: "1px solid var(--line)",
              color: "var(--muted)",
              fontSize: 12,
              padding: "5px 12px",
              marginTop: 14,
              borderRadius: 999,
              transform: "none",
            }}
          >
            {advanced ? "▲" : "▼"} Conditions
          </button>

          {advanced && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 16, marginTop: 14, alignItems: "center" }}>
              <div>
                <label>Humidity — {Math.round(humidity * 100)}%</label>
                <input type="range" min={0} max={1} step={0.01} value={humidity} onChange={(e) => setHumidity(Number(e.target.value))} />
              </div>
              <label style={{ marginBottom: 0, display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 13, textTransform: "none", letterSpacing: 0, color: "var(--ink)" }}>
                <input type="checkbox" checked={dew} onChange={(e) => setDew(e.target.checked)} />
                Dew (2nd innings)
              </label>
            </div>
          )}
        </div>

        {error && (
          <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 10, padding: "10px 14px", color: "#f87171", fontSize: 13, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "15px",
            fontSize: 16,
            fontWeight: 700,
            borderRadius: 12,
            background: `linear-gradient(90deg, ${selectedMode.color}, ${selectedMode.color}bb)`,
            color: "#fff",
            border: "none",
            letterSpacing: "0.03em",
          }}
        >
          {loading ? "Starting…" : mode === "quicksim" ? `⚡ Simulate — ${team1} vs ${team2}` : `🏏 Start Match — ${team1} vs ${team2}`}
        </button>
      </form>

      {/* Stats bar */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginTop: 24 }}>
        {[
          { label: "Teams", val: "8" },
          { label: "Players", val: "120" },
          { label: "Phase Engine", val: "PP/MID/DEATH" },
          { label: "Simulation", val: "Ball-by-Ball" },
        ].map(({ label, val }) => (
          <div key={label} className="kpi">
            <div className="small">{label}</div>
            <strong>{val}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
