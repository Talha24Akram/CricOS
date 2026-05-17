"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import CricketField from "@/components/CricketField";
import BattingControls from "@/components/BattingControls";
import BowlingControls from "@/components/BowlingControls";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

interface BallEvent {
  over: number;
  ball: number;
  innings: number;
  striker: string;
  bowler: string;
  outcome: string;
  runs: number;
  wicket: boolean;
  score_after: number;
  wickets_after: number;
  shot_zone?: string;
  delivery_type?: string;
  mindset?: string;
}

interface CardLine {
  player_id: number;
  player_name: string;
  runs?: number;
  balls?: number;
  fours?: number;
  sixes?: number;
  out?: boolean;
  wickets?: number;
  runs_conceded?: number;
}

interface GameState {
  session_id: string;
  mode: string;
  status: string;
  team1: string;
  team2: string;
  pending_action: string;
  innings: number;
  batting_team: string;
  bowling_team: string;
  score: number;
  wickets: number;
  balls: number;
  target: number | null;
  striker_id: number;
  non_striker_id: number;
  current_bowler_id: number;
  batting_card: Record<string, CardLine>;
  bowling_card: Record<string, CardLine>;
  events: BallEvent[];
  over_summary: string[];
  last_ball: BallEvent | null;
  user_controls_batting: boolean;
  user_controls_bowling: boolean;
  mindset_map: Record<string, string>;
  team1_lineup: number[];
  team2_lineup: number[];
  team1_captain_id: number;
  team2_captain_id: number;
  winner: string | null;
  margin: string | null;
  innings1: unknown;
  innings2: unknown;
}

const OUTCOME_COLORS: Record<string, string> = {
  "0":    "#71717a",
  dot:    "#71717a",
  "1":    "#d4d4d8",
  "2":    "#93c5fd",
  "3":    "#c4b5fd",
  "4":    "#34d399",
  "6":    "#fbbf24",
  wicket: "#f87171",
};

const OUTCOME_BG: Record<string, string> = {
  "4":    "rgba(52,211,153,0.15)",
  "6":    "rgba(251,191,36,0.15)",
  wicket: "rgba(248,113,113,0.15)",
};

function formatOvers(balls: number) {
  return `${Math.floor(balls / 6)}.${balls % 6}`;
}

function runRate(runs: number, balls: number) {
  if (balls === 0) return "0.00";
  return ((runs / balls) * 6).toFixed(2);
}

function requiredRate(target: number | null, score: number, balls: number) {
  if (!target) return null;
  const rem = 120 - balls;
  if (rem <= 0) return null;
  return (((target - score + 1) / rem) * 6).toFixed(2);
}

function getPhase(balls: number): "powerplay" | "middle" | "death" {
  const ov = Math.floor(balls / 6);
  if (ov < 6)  return "powerplay";
  if (ov < 16) return "middle";
  return "death";
}

const PHASE_CONFIG = {
  powerplay: { label: "⚡ POWERPLAY", color: "#34d399", bg: "rgba(52,211,153,0.12)" },
  middle:    { label: "⚾ MIDDLE",    color: "#fbbf24", bg: "rgba(251,191,36,0.10)" },
  death:     { label: "🔥 DEATH",    color: "#f87171", bg: "rgba(248,113,113,0.12)" },
};

export default function GamePage() {
  const router    = useRouter();
  const params    = useSearchParams();
  const sessionId = params.get("session") || "";

  const [gs,      setGs]      = useState<GameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting,  setActing]  = useState(false);
  const [error,   setError]   = useState("");
  const [fielders, setFielders] = useState<string[]>([]);
  const feedRef = useRef<HTMLDivElement>(null);

  const fetchState = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res  = await fetch(`${API}/game/${sessionId}`);
      const data: GameState = await res.json();
      setGs(data);
    } catch {
      setError("Failed to load game state");
    }
  }, [sessionId]);

  useEffect(() => {
    fetchState().finally(() => setLoading(false));
  }, [fetchState]);

  // Auto-advance AI turns
  useEffect(() => {
    if (!gs) return;
    const { pending_action, status } = gs;
    if (status === "completed") return;
    if (pending_action === "auto") {
      const t = setTimeout(() => sendAction("sim_ball", {}), 300);
      return () => clearTimeout(t);
    }
    if (pending_action === "start_innings2") {
      const t = setTimeout(() => sendAction("start_innings2", {}), 1500);
      return () => clearTimeout(t);
    }
  }, [gs?.pending_action, gs?.status]);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [gs?.events?.length]);

  const sendAction = async (action_type: string, payload: unknown) => {
    if (!sessionId || acting) return;
    setActing(true);
    setError("");
    try {
      const res = await fetch(`${API}/game/${sessionId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type, payload }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data: GameState = await res.json();
      setGs(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setActing(false);
    }
  };

  const toggleFielder = (zone: string) => {
    setFielders((prev) => prev.includes(zone) ? prev.filter((z) => z !== zone) : [...prev, zone]);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300, color: "var(--muted)" }}>
        Loading match…
      </div>
    );
  }

  if (!gs) {
    return (
      <div style={{ textAlign: "center", padding: 60, color: "#f87171" }}>
        Session not found.
      </div>
    );
  }

  // ── Match complete ──────────────────────────────────────────────────────────
  if (gs.status === "completed") {
    return (
      <div style={{ maxWidth: 560, margin: "40px auto", textAlign: "center" }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>🏆</div>
        <h1 style={{ fontSize: 42, color: "#fbbf24", marginBottom: 6 }}>{gs.winner}</h1>
        <p style={{ color: "var(--muted)", fontSize: 17, marginBottom: 32 }}>won by {gs.margin}</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 32 }}>
          {[
            { label: `1st Innings — ${gs.team1}`, data: gs.innings1 as {runs:number;wickets:number} | null },
            { label: `2nd Innings — ${gs.team2}`, data: gs.innings2 as {runs:number;wickets:number} | null },
          ].map(({ label, data }) =>
            data ? (
              <div key={label} className="card" style={{ textAlign: "center" }}>
                <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 30, fontWeight: 700 }}>{data.runs}/{data.wickets}</div>
              </div>
            ) : null
          )}
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <button
            type="button"
            onClick={() => router.push("/")}
            style={{
              flex: 1, padding: "14px", fontSize: 15, fontWeight: 700, borderRadius: 12,
              background: "linear-gradient(90deg, var(--accent), #17b9ff)",
              color: "#041018", border: "none", transform: "none",
            }}
          >
            New Game
          </button>
          <button
            type="button"
            onClick={() => router.push("/stats")}
            style={{
              flex: 1, padding: "14px", fontSize: 15, fontWeight: 700, borderRadius: 12,
              background: "rgba(255,255,255,0.06)", color: "var(--muted)",
              border: "1px solid var(--line)", transform: "none",
            }}
          >
            View Stats
          </button>
        </div>
      </div>
    );
  }

  // ── In-match ────────────────────────────────────────────────────────────────
  const phase    = getPhase(gs.balls);
  const phaseConf = PHASE_CONFIG[phase];
  const isPowerplay = phase === "powerplay";
  const rr       = requiredRate(gs.target, gs.score, gs.balls);

  const userBatting = gs.user_controls_batting;
  const userBowling = gs.user_controls_bowling;
  const userTurn    = userBatting
    ? gs.pending_action === "batting_decision"
    : userBowling
    ? gs.pending_action === "bowling_decision"
    : false;

  const strikerLine = Object.values(gs.batting_card).find((c) => c.player_id === gs.striker_id);
  const bowlerLine  = Object.values(gs.bowling_card).find((c) => c.player_id === gs.current_bowler_id);
  const strikerName = strikerLine?.player_name || "Batter";
  const bowlerName  = bowlerLine?.player_name  || "Bowler";

  const currentMindset = (gs.mindset_map[String(gs.striker_id)] as "ultra_defensive" | "defensive" | "balanced" | "aggressive" | "ultra_aggressive") || "balanced";

  // Progress bar: 0-120 balls
  const progressPct = (gs.balls / 120) * 100;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* ── Score banner ── */}
      <div className="card" style={{ marginBottom: 14 }}>
        {/* Innings progress bar */}
        <div style={{ height: 4, background: "var(--line)", borderRadius: 999, marginBottom: 12, overflow: "hidden" }}>
          <div style={{
            height: "100%", width: `${progressPct}%`,
            background: `linear-gradient(90deg, ${phaseConf.color}88, ${phaseConf.color})`,
            borderRadius: 999, transition: "width 0.3s ease",
          }} />
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          {/* Score */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span style={{ fontSize: 13, color: "var(--muted)", fontWeight: 500 }}>{gs.batting_team}</span>
            <span style={{ fontSize: 38, fontWeight: 700, lineHeight: 1, letterSpacing: "-1px" }}>
              {gs.score}/{gs.wickets}
            </span>
            <span style={{ fontSize: 14, color: "var(--muted)" }}>({formatOvers(gs.balls)} ov)</span>
          </div>

          {/* Phase badge */}
          <div style={{
            padding: "5px 12px", borderRadius: 999,
            background: phaseConf.bg,
            border: `1px solid ${phaseConf.color}44`,
            color: phaseConf.color, fontSize: 12, fontWeight: 700,
          }}>
            {phaseConf.label}
          </div>

          {/* Rates */}
          <div style={{ display: "flex", gap: 20, fontSize: 13 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "var(--muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>RR</div>
              <div style={{ fontWeight: 700 }}>{runRate(gs.score, gs.balls)}</div>
            </div>
            {rr && (
              <div style={{ textAlign: "center" }}>
                <div style={{ color: "var(--muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>RRR</div>
                <div style={{ fontWeight: 700, color: "#fbbf24" }}>{rr}</div>
              </div>
            )}
            {gs.target && (
              <div style={{ textAlign: "center" }}>
                <div style={{ color: "var(--muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>Target</div>
                <div style={{ fontWeight: 700, color: "#34d399" }}>{gs.target + 1}</div>
              </div>
            )}
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "var(--muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>Innings</div>
              <div style={{ fontWeight: 700 }}>{gs.innings}</div>
            </div>
          </div>

          {/* Bowling team */}
          <div style={{ fontSize: 12, color: "var(--muted)" }}>
            {gs.bowling_team} bowling
          </div>
        </div>

        {/* Current batters + bowler quick line */}
        {strikerLine && bowlerLine && (
          <div style={{
            display: "flex", alignItems: "center", gap: 16, marginTop: 10,
            paddingTop: 10, borderTop: "1px solid var(--line)", fontSize: 12,
          }}>
            <span style={{ color: "#34d399" }}>
              🏏 <strong>{strikerLine.player_name}*</strong>{" "}
              <span style={{ color: "var(--muted)" }}>{strikerLine.runs}({strikerLine.balls})</span>
            </span>
            {gs.non_striker_id !== gs.striker_id && (() => {
              const ns = Object.values(gs.batting_card).find((c) => c.player_id === gs.non_striker_id);
              return ns ? (
                <span style={{ color: "var(--muted)" }}>
                  {ns.player_name} {ns.runs}({ns.balls})
                </span>
              ) : null;
            })()}
            <span style={{ marginLeft: "auto", color: "#93c5fd" }}>
              🎳 <strong>{bowlerLine.player_name}</strong>{" "}
              <span style={{ color: "var(--muted)" }}>{bowlerLine.wickets}-{bowlerLine.runs_conceded} ({formatOvers(bowlerLine.balls || 0)})</span>
            </span>
          </div>
        )}
      </div>

      {/* ── Main grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 14 }}>
        {/* Left: field + controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="card" style={{ padding: 12 }}>
            <CricketField
              fielders={fielders}
              onZoneClick={userBowling && gs.pending_action === "bowling_decision" ? toggleFielder : undefined}
              interactive={userBowling && gs.pending_action === "bowling_decision"}
              lastShotZone={gs.last_ball?.shot_zone}
              trajectory={gs.last_ball?.shot_zone ? { from: "pitch", to: gs.last_ball.shot_zone } : null}
              isPowerplay={isPowerplay}
              phase={phase}
            />
          </div>

          {/* Controls panel */}
          {userTurn && (
            <div className="card">
              {userBatting && gs.pending_action === "batting_decision" && (
                <BattingControls
                  currentMindset={currentMindset}
                  strikerName={strikerName}
                  onMindsetChange={(m) => sendAction("set_mindset", { player_id: gs.striker_id, mindset: m })}
                  onSimBall={() => sendAction("sim_ball", {})}
                  onSimOver={() => sendAction("sim_over", {})}
                  disabled={acting}
                />
              )}
              {userBowling && gs.pending_action === "bowling_decision" && (
                <BowlingControls
                  bowlerName={bowlerName}
                  fielders={fielders}
                  onBowl={(opts) => sendAction("bowl", opts)}
                  disabled={acting}
                  isPowerplay={isPowerplay}
                />
              )}
            </div>
          )}

          {!userTurn && gs.status !== "completed" && (
            <div className="card" style={{ textAlign: "center", padding: "20px", color: "var(--muted)" }}>
              {acting
                ? <span style={{ color: "var(--accent)" }}>⚙ Simulating…</span>
                : <span>🤖 AI is thinking…</span>}
            </div>
          )}

          {/* Last ball result */}
          {gs.last_ball && (
            <div
              className="card"
              style={{
                background: OUTCOME_BG[gs.last_ball.outcome]
                  ? `linear-gradient(160deg, ${OUTCOME_BG[gs.last_ball.outcome]}, rgba(9,13,20,0.99))`
                  : undefined,
              }}
            >
              <div style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                Last Ball
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{
                  fontSize: 28, fontWeight: 700,
                  color: OUTCOME_COLORS[gs.last_ball.outcome] || "var(--ink)",
                  minWidth: 36,
                }}>
                  {gs.last_ball.outcome === "wicket" ? "W" : gs.last_ball.outcome === "dot" ? "·" : gs.last_ball.outcome}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>
                    <span style={{ color: "var(--ink)" }}>{gs.last_ball.striker}</span>
                    <span style={{ color: "var(--muted)" }}> vs </span>
                    <span style={{ color: "var(--ink)" }}>{gs.last_ball.bowler}</span>
                  </div>
                  {gs.last_ball.outcome === "wicket" && (
                    <div style={{ fontSize: 11, color: "#f87171", marginTop: 2 }}>WICKET!</div>
                  )}
                  {gs.last_ball.outcome === "4" && (
                    <div style={{ fontSize: 11, color: "#34d399", marginTop: 2 }}>FOUR!</div>
                  )}
                  {gs.last_ball.outcome === "6" && (
                    <div style={{ fontSize: 11, color: "#fbbf24", marginTop: 2 }}>SIX!</div>
                  )}
                </div>
                <div style={{ textAlign: "right", fontSize: 11, color: "var(--muted)" }}>
                  {gs.last_ball.delivery_type && (
                    <div style={{ marginBottom: 2 }}>{gs.last_ball.delivery_type}</div>
                  )}
                  <div style={{ color: "var(--ink)", fontWeight: 600 }}>
                    {gs.last_ball.score_after}/{gs.last_ball.wickets_after}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: scorecards + feed */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Batting card */}
          <div className="card">
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 10 }}>
              Batting
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {Object.values(gs.batting_card)
                .filter((l) => (l.balls ?? 0) > 0 || l.player_id === gs.striker_id || l.player_id === gs.non_striker_id)
                .map((l) => (
                  <div key={l.player_id} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                    <div style={{ flex: 1, color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      <span style={{
                        color: l.player_id === gs.striker_id ? "#34d399" : "var(--ink)",
                        fontWeight: l.player_id === gs.striker_id ? 700 : 400,
                      }}>
                        {l.player_name}
                      </span>
                      {l.player_id === gs.striker_id && <span style={{ color: "#34d399", marginLeft: 3 }}>*</span>}
                    </div>
                    <span style={{ fontWeight: 700, color: "var(--ink)", minWidth: 22, textAlign: "right" }}>{l.runs ?? 0}</span>
                    <span style={{ color: "var(--muted)", minWidth: 28 }}>({l.balls ?? 0})</span>
                    {l.out && <span style={{ color: "#f87171", fontSize: 9 }}>OUT</span>}
                  </div>
                ))}
            </div>
          </div>

          {/* Bowling card */}
          <div className="card">
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 10 }}>
              Bowling
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {Object.values(gs.bowling_card).map((l) => (
                <div key={l.player_id} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                  <div style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <span style={{
                      color: l.player_id === gs.current_bowler_id ? "#93c5fd" : "var(--ink)",
                      fontWeight: l.player_id === gs.current_bowler_id ? 700 : 400,
                    }}>
                      {l.player_name}
                    </span>
                    {l.player_id === gs.current_bowler_id && <span style={{ color: "#93c5fd", marginLeft: 3 }}>▶</span>}
                  </div>
                  <span style={{ color: "var(--ink)", fontWeight: 600, minWidth: 36, textAlign: "right" }}>
                    {l.wickets}-{l.runs_conceded}
                  </span>
                  <span style={{ color: "var(--muted)", minWidth: 28 }}>{formatOvers(l.balls || 0)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ball-by-ball feed */}
          <div className="card" style={{ flex: 1 }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 8 }}>
              Ball Feed
            </div>
            <div ref={feedRef} style={{ maxHeight: 220, overflowY: "auto", display: "flex", flexDirection: "column", gap: 2 }}>
              {gs.events.slice(-40).map((e, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 11,
                    padding: "3px 6px",
                    borderRadius: 5,
                    background: e.outcome === "wicket" ? "rgba(248,113,113,0.08)"
                              : e.outcome === "6"      ? "rgba(251,191,36,0.06)"
                              : e.outcome === "4"      ? "rgba(52,211,153,0.06)"
                              : "transparent",
                  }}
                >
                  <span style={{ color: "var(--muted)", fontSize: 10, minWidth: 24 }}>
                    {e.over}.{e.ball}
                  </span>
                  <span style={{
                    minWidth: 18, textAlign: "center", fontWeight: 700,
                    color: OUTCOME_COLORS[e.outcome] || "var(--ink)",
                  }}>
                    {e.outcome === "dot" ? "·" : e.outcome === "wicket" ? "W" : e.outcome}
                  </span>
                  <span style={{ color: "var(--muted)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {e.striker}
                  </span>
                  <span style={{ color: "var(--muted)", fontSize: 10, flexShrink: 0 }}>
                    {e.score_after}/{e.wickets_after}
                  </span>
                </div>
              ))}
              {gs.events.length === 0 && (
                <div style={{ color: "var(--muted)", fontSize: 11, textAlign: "center", padding: "16px 0" }}>
                  Match about to begin…
                </div>
              )}
            </div>
          </div>

          {/* Over summary */}
          {gs.over_summary.length > 0 && (
            <div className="card">
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 8 }}>
                Overs
              </div>
              <div style={{ maxHeight: 100, overflowY: "auto", display: "flex", flexDirection: "column", gap: 2 }}>
                {gs.over_summary.slice(-8).map((s, i) => (
                  <div key={i} style={{ fontSize: 11, color: "var(--muted)" }}>{s}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error toast */}
      {error && (
        <div style={{
          position: "fixed", bottom: 20, left: "50%", transform: "translateX(-50%)",
          background: "#7f1d1d", border: "1px solid #ef4444", color: "#fca5a5",
          padding: "10px 20px", borderRadius: 10, fontSize: 13, zIndex: 999,
        }}>
          {error}
        </div>
      )}
    </div>
  );
}
