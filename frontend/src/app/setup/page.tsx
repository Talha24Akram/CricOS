"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import PlayerCard from "@/components/PlayerCard";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

interface PlayerInfo {
  id: number;
  name: string;
  role: string;
  photo_url: string;
  overall?: number;
}

interface TeamData {
  id: number;
  name: string;
  squad: PlayerInfo[];
}

const ROLE_ORDER = ["batter", "wicket_keeper", "all_rounder", "bowler"];

export default function SetupPage() {
  const router   = useRouter();
  const params   = useSearchParams();
  const sessionId = params.get("session");
  const team1Name = params.get("team1") || "";
  const team2Name = params.get("team2") || "";
  const mode      = params.get("mode") || "user_vs_ai";

  const [squad,      setSquad]      = useState<PlayerInfo[]>([]);
  const [lineup,     setLineup]     = useState<number[]>([]);
  const [captainId,  setCaptainId]  = useState<number | null>(null);
  const [wkId,       setWkId]       = useState<number | null>(null);
  const [ratings,    setRatings]    = useState<Record<number, number>>({});
  const [loading,    setLoading]    = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error,      setError]      = useState("");
  const [filter,     setFilter]     = useState<string>("all");

  const userTeam = team1Name;

  useEffect(() => {
    if (!userTeam) return;
    fetch(`${API}/teams`)
      .then((r) => r.json())
      .then(async (teams: TeamData[]) => {
        const team = teams.find((t) => t.name === userTeam);
        if (!team) return;

        // Sort squad by role
        const sorted = [...team.squad].sort((a, b) => {
          return (ROLE_ORDER.indexOf(a.role) ?? 4) - (ROLE_ORDER.indexOf(b.role) ?? 4);
        });
        setSquad(sorted);

        const overalls: Record<number, number> = {};
        await Promise.all(
          sorted.map(async (p) => {
            try {
              const r = await fetch(`${API}/players/${p.id}`);
              const d = await r.json();
              overalls[p.id] = d.overall || 50;
            } catch {
              overalls[p.id] = 50;
            }
          })
        );
        setRatings(overalls);

        // Auto-select first 11 (best rated)
        const sorted11 = [...sorted].sort((a, b) => (overalls[b.id] || 50) - (overalls[a.id] || 50));
        const first11  = sorted11.slice(0, 11).map((p) => p.id);
        setLineup(first11);
        setCaptainId(first11[0]);
        const wk = sorted.find((p) => p.role === "wicket_keeper");
        setWkId(wk ? wk.id : first11[0]);
      })
      .finally(() => setLoading(false));
  }, [userTeam]);

  const togglePlayer = (id: number) => {
    if (lineup.includes(id)) {
      if (lineup.length > 1) {
        setLineup((prev) => prev.filter((x) => x !== id));
        if (captainId === id) setCaptainId(lineup.find((x) => x !== id) || null);
        if (wkId === id) setWkId(null);
      }
    } else if (lineup.length < 11) {
      setLineup((prev) => [...prev, id]);
    }
  };

  const handleSubmit = async () => {
    if (lineup.length !== 11) { setError("Select exactly 11 players."); return; }
    if (!captainId)            { setError("Select a captain."); return; }
    if (!wkId)                 { setError("Select a wicket-keeper."); return; }
    if (!sessionId)            { setError("No session found."); return; }
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API}/game/${sessionId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "set_lineup",
          payload: { team: "team1", player_ids: lineup, captain_id: captainId, wk_id: wkId },
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      router.push(`/toss?session=${sessionId}&team1=${team1Name}&team2=${team2Name}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error submitting lineup");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300, color: "var(--muted)" }}>
        <span>Loading squad…</span>
      </div>
    );
  }

  const filteredSquad = filter === "all" ? squad : squad.filter((p) => p.role === filter);
  const slotsLeft = 11 - lineup.length;

  const ROLE_FILTERS = [
    { key: "all",            label: "All" },
    { key: "batter",         label: "Batters" },
    { key: "wicket_keeper",  label: "Keepers" },
    { key: "all_rounder",    label: "All-Rounders" },
    { key: "bowler",         label: "Bowlers" },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 6 }}>
          <h2 style={{ fontSize: 36, color: "var(--accent)" }}>Select Your XI</h2>
          <span style={{ color: "var(--muted)", fontSize: 15 }}>{userTeam} vs {team2Name}</span>
        </div>

        {/* Instruction banner */}
        <div style={{
          background: "rgba(0,209,178,0.08)",
          border: "1px solid rgba(0,209,178,0.25)",
          borderRadius: 10,
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 13,
          color: "var(--accent)",
        }}>
          <span style={{ fontSize: 18 }}>👆</span>
          <span>
            <strong>Click a player card</strong> to add or remove them from your XI.
            Then set <strong style={{ color: "#f59e0b" }}>Captain (C)</strong> and <strong style={{ color: "#a78bfa" }}>Wicket-Keeper (WK)</strong> using the buttons on each card.
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 20, alignItems: "start" }}>
        {/* Left: Squad */}
        <div>
          {/* Filters + count */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14, gap: 12, flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {ROLE_FILTERS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => setFilter(f.key)}
                  style={{
                    width: "auto",
                    padding: "5px 12px",
                    fontSize: 12,
                    fontWeight: 600,
                    borderRadius: 999,
                    background: filter === f.key ? "var(--accent)" : "rgba(255,255,255,0.05)",
                    color: filter === f.key ? "#041018" : "var(--muted)",
                    border: `1px solid ${filter === f.key ? "var(--accent)" : "var(--line)"}`,
                    transform: "none",
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 13, color: "var(--muted)" }}>
              <span style={{ color: lineup.length === 11 ? "#34d399" : "#f59e0b", fontWeight: 700, fontSize: 16 }}>{lineup.length}</span>
              <span>/11 selected</span>
              {slotsLeft > 0 && (
                <span style={{ marginLeft: 8, color: "#f59e0b" }}>· {slotsLeft} slot{slotsLeft !== 1 ? "s" : ""} left</span>
              )}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: 10 }}>
            {filteredSquad.map((p) => (
              <PlayerCard
                key={p.id}
                id={p.id}
                name={p.name}
                role={p.role}
                photo_url={p.photo_url}
                overall={ratings[p.id] || 50}
                isSelected={lineup.includes(p.id)}
                isCaptain={captainId === p.id}
                isWK={wkId === p.id}
                onClick={() => togglePlayer(p.id)}
                onCaptain={() => lineup.includes(p.id) && setCaptainId(p.id)}
                onWK={() => lineup.includes(p.id) && setWkId(p.id)}
                disabled={!lineup.includes(p.id) && lineup.length >= 11}
              />
            ))}
          </div>
        </div>

        {/* Right: Batting order + confirm */}
        <div style={{ position: "sticky", top: 74 }}>
          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 14 }}>
              Batting Order
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {Array.from({ length: 11 }, (_, i) => {
                const id = lineup[i];
                const p  = id ? squad.find((s) => s.id === id) : null;
                return (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "7px 10px",
                      borderRadius: 8,
                      background: p ? "rgba(0,209,178,0.06)" : "rgba(255,255,255,0.02)",
                      border: `1px solid ${p ? "rgba(0,209,178,0.2)" : "var(--line)"}`,
                      minHeight: 40,
                    }}
                  >
                    <span style={{ color: "var(--muted)", fontSize: 12, width: 18, textAlign: "right", flexShrink: 0 }}>
                      {i + 1}.
                    </span>
                    {p ? (
                      <>
                        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--ink)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {p.name}
                        </span>
                        <div style={{ display: "flex", gap: 3 }}>
                          {captainId === id && (
                            <span style={{ fontSize: 10, background: "#f59e0b", color: "#000", padding: "1px 5px", borderRadius: 4, fontWeight: 700 }}>C</span>
                          )}
                          {wkId === id && (
                            <span style={{ fontSize: 10, background: "#7c3aed", color: "#fff", padding: "1px 5px", borderRadius: 4, fontWeight: 700 }}>WK</span>
                          )}
                        </div>
                      </>
                    ) : (
                      <span style={{ fontSize: 11, color: "var(--muted)", opacity: 0.4, fontStyle: "italic" }}>
                        — empty slot —
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Status checks */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
            {[
              { ok: lineup.length === 11, label: "11 players selected", detail: `${lineup.length}/11` },
              { ok: !!captainId,          label: "Captain set",         detail: captainId ? squad.find(p => p.id === captainId)?.name : "Not set" },
              { ok: !!wkId,              label: "Wicket-keeper set",   detail: wkId ? squad.find(p => p.id === wkId)?.name : "Not set" },
            ].map(({ ok, label, detail }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                <span style={{ fontSize: 14 }}>{ok ? "✅" : "⬜"}</span>
                <span style={{ color: ok ? "var(--ink)" : "var(--muted)" }}>{label}</span>
                <span style={{ marginLeft: "auto", color: ok ? "#34d399" : "var(--muted)", fontSize: 11 }}>{detail}</span>
              </div>
            ))}
          </div>

          {error && (
            <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "8px 12px", color: "#f87171", fontSize: 12, marginBottom: 10 }}>
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={submitting || lineup.length !== 11 || !captainId || !wkId}
            style={{
              width: "100%",
              padding: "14px",
              fontSize: 15,
              fontWeight: 700,
              borderRadius: 12,
              background: lineup.length === 11 && captainId && wkId
                ? "linear-gradient(90deg, var(--accent), #17b9ff)"
                : "var(--bg-alt)",
              color: lineup.length === 11 && captainId && wkId ? "#041018" : "var(--muted)",
              border: "none",
            }}
          >
            {submitting ? "Confirming…" : "Confirm Lineup → Toss"}
          </button>
        </div>
      </div>
    </div>
  );
}
