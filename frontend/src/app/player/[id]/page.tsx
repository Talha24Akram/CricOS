"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { RadarRatings } from "@/components/RadarRatings";
import { apiGet } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

const ROLE_LABELS: Record<string, string> = {
  batter: "Batter",
  bowler: "Bowler",
  all_rounder: "All-Rounder",
  wicket_keeper: "Wicket-Keeper",
};

export default function PlayerProfilePage() {
  const params = useParams<{ id: string }>();
  const [player, setPlayer] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [imgErr, setImgErr] = useState(false);

  useEffect(() => {
    if (!params?.id) return;
    apiGet(`/players/${params.id}`).then(setPlayer).catch(() => setPlayer(null));
    fetch(`${API}/players/${params.id}/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats(null));
  }, [params?.id]);

  if (!player) return <div className="card">Player not found or ratings unavailable.</div>;

  const overall = player.overall || 50;
  const overallColor =
    overall >= 85 ? "#fbbf24" : overall >= 70 ? "#34d399" : overall >= 55 ? "#60a5fa" : "#9ca3af";

  return (
    <section className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
      {/* Left: identity + career stats */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <article className="card" style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
          {/* Photo */}
          <div style={{
            width: 96, height: 96, borderRadius: "50%", overflow: "hidden",
            background: "#3f3f46", flexShrink: 0,
          }}>
            {player.photo_url && !imgErr ? (
              <img
                src={player.photo_url}
                alt={player.name}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                onError={() => setImgErr(true)}
              />
            ) : (
              <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>👤</div>
            )}
          </div>

          {/* Info */}
          <div>
            <h2 style={{ fontSize: 28, marginBottom: 4 }}>{player.name}</h2>
            <p style={{ color: "#a1a1aa", marginBottom: 2 }}>
              {ROLE_LABELS[player.role] || player.role} ·{" "}
              {player.batting_style || "Unknown bat"} ·{" "}
              {player.bowling_style || "Unknown bowl"}
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
              <span style={{
                fontSize: 28, fontWeight: "bold", color: overallColor,
                background: "#27272a", borderRadius: 8, padding: "4px 12px",
              }}>
                {overall}
              </span>
              <span style={{ color: "#71717a", fontSize: 13 }}>Overall</span>
            </div>
          </div>
        </article>

        {/* Sim stats */}
        {stats && (
          <article className="card">
            <h3 style={{ marginBottom: 12 }}>Sim Career Stats</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {/* Batting */}
              <div>
                <div style={{ color: "#71717a", fontSize: 11, textTransform: "uppercase", marginBottom: 8 }}>Batting</div>
                <div className="kpis" style={{ gap: 8 }}>
                  {[
                    { label: "Matches", val: stats.sim_batting?.matches || 0 },
                    { label: "Runs", val: stats.sim_batting?.runs || 0 },
                    { label: "Avg", val: stats.sim_batting?.average || "-" },
                    { label: "SR", val: stats.sim_batting?.strike_rate || "-" },
                    { label: "4s", val: stats.sim_batting?.fours || 0 },
                    { label: "6s", val: stats.sim_batting?.sixes || 0 },
                  ].map(({ label, val }) => (
                    <div key={label} className="kpi">
                      <div className="small">{label}</div>
                      <strong>{val}</strong>
                    </div>
                  ))}
                </div>
              </div>
              {/* Bowling */}
              <div>
                <div style={{ color: "#71717a", fontSize: 11, textTransform: "uppercase", marginBottom: 8 }}>Bowling</div>
                <div className="kpis" style={{ gap: 8 }}>
                  {[
                    { label: "Wickets", val: stats.sim_bowling?.wickets || 0 },
                    { label: "Econ", val: stats.sim_bowling?.economy || "-" },
                    { label: "Avg", val: stats.sim_bowling?.average || "-" },
                    { label: "SR", val: stats.sim_bowling?.strike_rate || "-" },
                  ].map(({ label, val }) => (
                    <div key={label} className="kpi">
                      <div className="small">{label}</div>
                      <strong>{val}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </article>
        )}
      </div>

      {/* Right: radar ratings */}
      <RadarRatings ratings={player.ratings || {}} />
    </section>
  );
}
