"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { RadarRatings } from "@/components/RadarRatings";
import { apiGet } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

const ROLE_LABELS: Record<string, string> = {
  batter:        "Batter",
  bowler:        "Bowler",
  all_rounder:   "All-Rounder",
  wicket_keeper: "Wicket-Keeper",
};

const ROLE_COLORS: Record<string, string> = {
  batter:        "#34d399",
  bowler:        "#60a5fa",
  all_rounder:   "#fbbf24",
  wicket_keeper: "#c084fc",
};

function StatBox({ label, val, color }: { label: string; val: string | number; color?: string }) {
  return (
    <div style={{
      textAlign: "center",
      background: "rgba(255,255,255,0.03)",
      border: "1px solid var(--line)",
      borderRadius: 10, padding: "10px 8px",
    }}>
      <div style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || "var(--ink)" }}>
        {val === 0 || val === "0" ? <span style={{ opacity: 0.35 }}>—</span> : val}
      </div>
    </div>
  );
}

function RatingBar({ label, val, color }: { label: string; val: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ fontSize: 11, color: "var(--muted)", minWidth: 90, textAlign: "right" }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: "var(--line)", borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: 999, transition: "width 0.4s ease" }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 28 }}>{val}</span>
    </div>
  );
}

export default function PlayerProfilePage() {
  const params = useParams<{ id: string }>();
  const [player, setPlayer] = useState<any>(null);
  const [stats,  setStats]  = useState<any>(null);
  const [imgErr, setImgErr] = useState(false);

  useEffect(() => {
    if (!params?.id) return;
    apiGet(`/players/${params.id}`).then(setPlayer).catch(() => setPlayer(null));
    fetch(`${API}/players/${params.id}/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats(null));
  }, [params?.id]);

  if (!player) {
    return (
      <div style={{ textAlign: "center", padding: 60, color: "var(--muted)" }}>
        Player not found.
      </div>
    );
  }

  const overall = player.overall || 50;
  const overallColor = overall >= 85 ? "#fbbf24" : overall >= 70 ? "#34d399" : overall >= 55 ? "#60a5fa" : "#71717a";
  const roleColor = ROLE_COLORS[player.role] || "#71717a";
  const roleLabel = ROLE_LABELS[player.role] || player.role;
  const ratings   = player.ratings || {};

  const RATING_GROUPS = [
    {
      title: "Batting", color: "#34d399",
      keys: ["power", "timing", "aggression", "temperament", "clutch", "pace_handling", "spin_handling", "death_batting"],
    },
    {
      title: "Bowling", color: "#60a5fa",
      keys: ["pace", "swing", "seam", "spin", "control", "variations", "yorkers", "death_bowling"],
    },
    {
      title: "Fielding", color: "#fbbf24",
      keys: ["catching", "ground_fielding", "throwing", "range_"],
    },
    {
      title: "Wicket-Keeping", color: "#c084fc",
      keys: ["glove_work", "stumping", "diving_reflexes", "wk_footwork"],
    },
    {
      title: "Leadership", color: "#fb923c",
      keys: ["captaincy", "match_reading", "man_management"],
    },
  ];

  const RATING_LABELS: Record<string, string> = {
    power: "Power", timing: "Timing", aggression: "Aggression", temperament: "Temperament",
    clutch: "Clutch", pace_handling: "vs Pace", spin_handling: "vs Spin", death_batting: "Death Bat",
    pace: "Pace", swing: "Swing", seam: "Seam", spin: "Spin", control: "Control",
    variations: "Variations", yorkers: "Yorkers", death_bowling: "Death Bowl",
    catching: "Catching", ground_fielding: "Ground", throwing: "Throwing", range_: "Range",
    glove_work: "Gloves", stumping: "Stumping", diving_reflexes: "Reflexes", wk_footwork: "Footwork",
    captaincy: "Captaincy", match_reading: "Reading", man_management: "Man Mgmt",
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      {/* Identity card */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
          <div style={{
            width: 100, height: 100, borderRadius: "50%", overflow: "hidden",
            background: "#1e304a", flexShrink: 0,
            border: `3px solid ${overallColor}44`,
            boxShadow: `0 0 20px ${overallColor}22`,
          }}>
            {player.photo_url && !imgErr ? (
              <img src={player.photo_url} alt={player.name}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                onError={() => setImgErr(true)} />
            ) : (
              <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 38 }}>
                👤
              </div>
            )}
          </div>

          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
              <h2 style={{ fontSize: 34, color: "var(--ink)" }}>{player.name}</h2>
              <span style={{
                fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 999,
                background: `${roleColor}18`, border: `1px solid ${roleColor}44`, color: roleColor,
              }}>
                {roleLabel}
              </span>
            </div>
            <div style={{ color: "var(--muted)", fontSize: 13, marginBottom: 12 }}>
              {player.batting_style && <span>{player.batting_style}</span>}
              {player.batting_style && player.bowling_style && <span style={{ margin: "0 8px", opacity: 0.4 }}>·</span>}
              {player.bowling_style && <span>{player.bowling_style}</span>}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                fontSize: 36, fontWeight: 700, color: overallColor,
                background: `${overallColor}15`, border: `1px solid ${overallColor}44`,
                borderRadius: 10, padding: "4px 14px", lineHeight: 1.2,
              }}>
                {overall}
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>Overall Rating</div>
                <div style={{ fontSize: 12, color: overallColor, fontWeight: 600 }}>
                  {overall >= 90 ? "World Class" : overall >= 80 ? "Elite" : overall >= 70 ? "Quality" : overall >= 60 ? "Good" : "Developing"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Sim Career Stats */}
          {stats && (
            <div className="card">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 14 }}>
                Sim Career Stats
              </div>
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: "#34d399", fontWeight: 600, marginBottom: 8 }}>🏏 Batting</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                  <StatBox label="Matches" val={stats.sim_batting?.matches ?? 0} />
                  <StatBox label="Runs"    val={stats.sim_batting?.runs ?? 0}    color="#34d399" />
                  <StatBox label="Avg"     val={stats.sim_batting?.average || "—"} />
                  <StatBox label="SR"      val={stats.sim_batting?.strike_rate || "—"} />
                  <StatBox label="4s"      val={stats.sim_batting?.fours ?? 0}   color="#34d399" />
                  <StatBox label="6s"      val={stats.sim_batting?.sixes ?? 0}   color="#fbbf24" />
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: "#60a5fa", fontWeight: 600, marginBottom: 8 }}>🎳 Bowling</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                  <StatBox label="Wickets" val={stats.sim_bowling?.wickets ?? 0} color="#f87171" />
                  <StatBox label="Economy" val={stats.sim_bowling?.economy || "—"} />
                  <StatBox label="Avg"     val={stats.sim_bowling?.average || "—"} />
                </div>
              </div>
            </div>
          )}

          {/* Rating bars */}
          {Object.keys(ratings).length > 0 && (
            <div className="card">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 14 }}>
                Attribute Ratings
              </div>
              {RATING_GROUPS.map(({ title, color, keys }) => {
                const present = keys.filter((k) => ratings[k] !== undefined);
                if (!present.length) return null;
                return (
                  <div key={title} style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, color, fontWeight: 600, marginBottom: 8 }}>{title}</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {present.map((k) => (
                        <RatingBar key={k} label={RATING_LABELS[k] || k} val={ratings[k]} color={color} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Radar chart */}
        <div>
          <RadarRatings ratings={ratings} />
        </div>
      </div>
    </div>
  );
}
