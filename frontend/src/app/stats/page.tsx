"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

interface PlayerStats {
  player_id: number;
  name: string;
  role: string;
  photo_url: string;
  overall: number;
  sim_batting: {
    matches: number;
    runs: number;
    balls_faced: number;
    average: number;
    strike_rate: number;
    fours: number;
    sixes: number;
    dismissals: number;
  };
  sim_bowling: {
    wickets: number;
    balls_bowled: number;
    runs_conceded: number;
    average: number;
    economy: number;
    strike_rate: number;
  };
}

const TEAMS = ["India", "Pakistan", "Australia", "England", "New Zealand", "South Africa", "West Indies", "Sri Lanka", "Bangladesh", "Afghanistan", "Zimbabwe", "Ireland"];

const ROLE_LABELS: Record<string, string> = {
  batter:         "BAT",
  bowler:         "BOWL",
  all_rounder:    "AR",
  wicket_keeper:  "WK",
};

const ROLE_COLORS: Record<string, string> = {
  batter:         "#34d399",
  bowler:         "#60a5fa",
  all_rounder:    "#fbbf24",
  wicket_keeper:  "#c084fc",
};

function OverallBadge({ val }: { val: number }) {
  const color = val >= 85 ? "#fbbf24" : val >= 70 ? "#34d399" : val >= 55 ? "#60a5fa" : "#71717a";
  return (
    <span style={{
      display: "inline-block",
      minWidth: 32, padding: "2px 6px",
      borderRadius: 6,
      background: `${color}18`,
      border: `1px solid ${color}44`,
      color, fontSize: 12, fontWeight: 700,
      textAlign: "center",
    }}>
      {val}
    </span>
  );
}

function ImgWithFallback({ src, name }: { src: string; name: string }) {
  const [err, setErr] = useState(false);
  return (
    <div style={{ width: 32, height: 32, borderRadius: "50%", overflow: "hidden", background: "#1e304a", flexShrink: 0 }}>
      {src && !err
        ? <img src={src} alt={name} style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={() => setErr(true)} />
        : <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>👤</div>
      }
    </div>
  );
}

type SortKey = "runs" | "average" | "strike_rate" | "fours" | "sixes" | "wickets" | "economy" | "bowling_average";

export default function StatsPage() {
  const [team,    setTeam]    = useState(TEAMS[0]);
  const [stats,   setStats]   = useState<PlayerStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab,     setTab]     = useState<"batting" | "bowling">("batting");
  const [sortKey, setSortKey] = useState<SortKey>("runs");

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/teams/${encodeURIComponent(team)}/stats`)
      .then((r) => r.json())
      .then((d) => setStats(Array.isArray(d) ? d : []))
      .finally(() => setLoading(false));
  }, [team]);

  // Switch default sort when tab changes
  useEffect(() => {
    setSortKey(tab === "batting" ? "runs" : "wickets");
  }, [tab]);

  const sorted = [...stats].sort((a, b) => {
    switch (sortKey) {
      case "runs":             return b.sim_batting.runs - a.sim_batting.runs;
      case "average":          return b.sim_batting.average - a.sim_batting.average;
      case "strike_rate":      return b.sim_batting.strike_rate - a.sim_batting.strike_rate;
      case "fours":            return b.sim_batting.fours - a.sim_batting.fours;
      case "sixes":            return b.sim_batting.sixes - a.sim_batting.sixes;
      case "wickets":          return b.sim_bowling.wickets - a.sim_bowling.wickets;
      case "economy":          return (a.sim_bowling.economy || 999) - (b.sim_bowling.economy || 999);
      case "bowling_average":  return (a.sim_bowling.average || 999) - (b.sim_bowling.average || 999);
      default:                 return 0;
    }
  });

  const SortTh = ({ label, k }: { label: string; k: SortKey }) => (
    <th
      onClick={() => setSortKey(k)}
      style={{
        textAlign: "center", padding: "10px 10px",
        cursor: "pointer", userSelect: "none",
        color: sortKey === k ? "var(--accent)" : "var(--muted)",
        fontSize: 11, fontWeight: 700,
        textTransform: "uppercase", letterSpacing: "0.06em",
        whiteSpace: "nowrap",
      }}
    >
      {label}{sortKey === k ? " ▼" : ""}
    </th>
  );

  const matchesPlayed = stats.reduce((n, p) => n + p.sim_batting.matches, 0);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 36, color: "var(--accent)", marginBottom: 4 }}>Player Stats</h2>
        <p style={{ color: "var(--muted)", fontSize: 13 }}>
          Sim career stats accumulated across all matches played on CricOS
        </p>
      </div>

      {/* Team selector */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
        {TEAMS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTeam(t)}
            style={{
              width: "auto",
              padding: "6px 14px",
              fontSize: 12,
              fontWeight: 600,
              borderRadius: 999,
              background: team === t ? "var(--accent)" : "rgba(255,255,255,0.04)",
              color: team === t ? "#041018" : "var(--muted)",
              border: `1px solid ${team === t ? "var(--accent)" : "var(--line)"}`,
              transform: "none",
              transition: "all 0.12s",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Batting / bowling tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 16, padding: "4px", background: "rgba(255,255,255,0.03)", borderRadius: 10, border: "1px solid var(--line)", width: "fit-content" }}>
        {(["batting", "bowling"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            style={{
              width: "auto",
              padding: "7px 20px",
              fontSize: 13,
              fontWeight: 600,
              borderRadius: 7,
              background: tab === t ? "var(--bg-card)" : "transparent",
              color: tab === t ? "var(--ink)" : "var(--muted)",
              border: "none",
              transform: "none",
              boxShadow: tab === t ? "0 1px 4px rgba(0,0,0,0.4)" : "none",
              transition: "all 0.15s",
            }}
          >
            {t === "batting" ? "🏏 Batting" : "🎳 Bowling"}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: "var(--muted)", padding: "40px 0", textAlign: "center" }}>
          Loading…
        </div>
      ) : (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--line)", borderRadius: 14, overflow: "hidden" }}>
          {sorted.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--muted)" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📊</div>
              <div style={{ fontSize: 15, marginBottom: 6 }}>No matches played yet</div>
              <div style={{ fontSize: 12, opacity: 0.6 }}>Play some matches to see stats appear here</div>
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--line)" }}>
                  <th style={{ textAlign: "left", padding: "10px 16px", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)", whiteSpace: "nowrap" }}>
                    Player
                  </th>
                  {tab === "batting" ? (
                    <>
                      <SortTh label="M"    k="runs" />
                      <SortTh label="Runs" k="runs" />
                      <SortTh label="Avg"  k="average" />
                      <SortTh label="SR"   k="strike_rate" />
                      <SortTh label="4s"   k="fours" />
                      <SortTh label="6s"   k="sixes" />
                    </>
                  ) : (
                    <>
                      <SortTh label="M"    k="wickets" />
                      <SortTh label="Wkts" k="wickets" />
                      <SortTh label="Avg"  k="bowling_average" />
                      <SortTh label="Econ" k="economy" />
                      <SortTh label="SR"   k="bowling_average" />
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {sorted.map((p, idx) => (
                  <tr
                    key={p.player_id}
                    style={{
                      borderBottom: "1px solid var(--line)",
                      transition: "background 0.1s",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.025)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <td style={{ padding: "10px 16px" }}>
                      <Link href={`/player/${p.player_id}`} style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
                        <span style={{ fontSize: 11, color: "var(--muted)", minWidth: 18 }}>{idx + 1}</span>
                        <ImgWithFallback src={p.photo_url} name={p.name} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13, color: "var(--ink)" }}>{p.name}</div>
                          <div style={{ display: "flex", gap: 5, alignItems: "center", marginTop: 2 }}>
                            <span style={{
                              fontSize: 9, fontWeight: 700, padding: "1px 5px", borderRadius: 4,
                              background: `${ROLE_COLORS[p.role] || "#71717a"}22`,
                              color: ROLE_COLORS[p.role] || "#71717a",
                            }}>
                              {ROLE_LABELS[p.role] || p.role.toUpperCase()}
                            </span>
                            <OverallBadge val={p.overall} />
                          </div>
                        </div>
                      </Link>
                    </td>
                    {tab === "batting" ? (
                      <>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_batting.matches}</td>
                        <td style={{ textAlign: "center", padding: "10px", fontWeight: 700, fontSize: 13 }}>{p.sim_batting.runs}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_batting.average || "—"}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_batting.strike_rate || "—"}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "#34d399", fontSize: 12, fontWeight: 600 }}>{p.sim_batting.fours}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "#fbbf24", fontSize: 12, fontWeight: 600 }}>{p.sim_batting.sixes}</td>
                      </>
                    ) : (
                      <>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_batting.matches}</td>
                        <td style={{ textAlign: "center", padding: "10px", fontWeight: 700, fontSize: 13 }}>{p.sim_bowling.wickets}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_bowling.average || "—"}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_bowling.economy || "—"}</td>
                        <td style={{ textAlign: "center", padding: "10px", color: "var(--muted)", fontSize: 12 }}>{p.sim_bowling.strike_rate || "—"}</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {matchesPlayed === 0 && !loading && (
        <div style={{ marginTop: 20, fontSize: 12, color: "var(--muted)", textAlign: "center" }}>
          Stats populate automatically after each completed match
        </div>
      )}
    </div>
  );
}
