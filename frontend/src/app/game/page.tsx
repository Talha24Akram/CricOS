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
  "0": "text-zinc-400",
  dot: "text-zinc-400",
  "1": "text-white",
  "2": "text-blue-300",
  "3": "text-purple-300",
  "4": "text-emerald-400 font-bold",
  "6": "text-yellow-400 font-bold",
  wicket: "text-red-400 font-bold",
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
  const remaining = 120 - balls;
  if (remaining <= 0) return null;
  return (((target - score + 1) / remaining) * 6).toFixed(2);
}

export default function GamePage() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionId = params.get("session") || "";

  const [gs, setGs] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState("");
  const [fielders, setFielders] = useState<string[]>([]);
  const [playerNames, setPlayerNames] = useState<Record<number, string>>({});
  const feedRef = useRef<HTMLDivElement>(null);

  const fetchState = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API}/game/${sessionId}`);
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
    if (status === "completed" || status === "innings1_done") return;
    if (pending_action === "auto") {
      const timer = setTimeout(() => {
        sendAction("sim_ball", {});
      }, 400);
      return () => clearTimeout(timer);
    }
    if (pending_action === "start_innings2") {
      const timer = setTimeout(() => {
        sendAction("start_innings2", {});
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [gs?.pending_action, gs?.status]);

  // Load player names
  useEffect(() => {
    if (!gs) return;
    const ids = new Set([
      ...Object.values(gs.batting_card).map((c) => c.player_id),
      ...Object.values(gs.bowling_card).map((c) => c.player_id),
    ]);
    ids.forEach(async (id) => {
      if (!playerNames[id]) {
        try {
          const r = await fetch(`${API}/players/${id}`);
          const d = await r.json();
          setPlayerNames((prev) => ({ ...prev, [id]: d.name }));
        } catch {}
      }
    });
  }, [gs]);

  // Scroll feed to bottom
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
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
    setFielders((prev) =>
      prev.includes(zone) ? prev.filter((z) => z !== zone) : [...prev, zone]
    );
  };

  const strikerName = gs
    ? Object.values(gs.batting_card).find((c) => c.player_id === gs.striker_id)?.player_name || "Batter"
    : "Batter";
  const bowlerName = gs
    ? Object.values(gs.bowling_card).find((c) => c.player_id === gs.current_bowler_id)?.player_name || "Bowler"
    : "Bowler";

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white text-xl">
        Loading match…
      </div>
    );
  }

  if (!gs) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-red-400">
        Session not found.
      </div>
    );
  }

  const rr = requiredRate(gs.target, gs.score, gs.balls);

  // Match complete screen
  if (gs.status === "completed") {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex flex-col items-center justify-center gap-6 p-6">
        <div className="text-5xl">🏆</div>
        <h1 className="text-3xl font-bold">{gs.winner}</h1>
        <p className="text-zinc-400 text-lg">won by {gs.margin}</p>
        <div className="grid grid-cols-2 gap-6 mt-4 text-center">
          {gs.innings1 && (
            <div className="bg-zinc-900 rounded-xl p-4">
              <div className="text-zinc-400 text-xs mb-1">1st Innings — {gs.team1}</div>
              <div className="text-2xl font-bold">{(gs.innings1 as {runs:number}).runs}/{(gs.innings1 as {wickets:number}).wickets}</div>
            </div>
          )}
          {gs.innings2 && (
            <div className="bg-zinc-900 rounded-xl p-4">
              <div className="text-zinc-400 text-xs mb-1">2nd Innings — {gs.team2}</div>
              <div className="text-2xl font-bold">{(gs.innings2 as {runs:number}).runs}/{(gs.innings2 as {wickets:number}).wickets}</div>
            </div>
          )}
        </div>
        <button
          onClick={() => router.push("/")}
          className="mt-4 px-8 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-bold"
        >
          New Game
        </button>
      </div>
    );
  }

  const userBatting = gs.user_controls_batting;
  const userBowling = gs.user_controls_bowling;
  const userTurn = userBatting
    ? gs.pending_action === "batting_decision"
    : userBowling
    ? gs.pending_action === "bowling_decision"
    : false;

  const currentMindset = (gs.mindset_map[String(gs.striker_id)] as "ultra_defensive" | "defensive" | "balanced" | "aggressive" | "ultra_aggressive") || "balanced";

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Score banner */}
      <div className="bg-zinc-900 border-b border-zinc-800 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between flex-wrap gap-2">
          <div>
            <span className="text-zinc-400 text-sm mr-2">{gs.batting_team}</span>
            <span className="text-3xl font-bold text-white">{gs.score}/{gs.wickets}</span>
            <span className="text-zinc-400 text-sm ml-3">({formatOvers(gs.balls)} ov)</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-zinc-500">RR <span className="text-white">{runRate(gs.score, gs.balls)}</span></span>
            {rr && <span className="text-zinc-500">RRR <span className="text-yellow-400">{rr}</span></span>}
            {gs.target && <span className="text-zinc-400">Target <span className="text-white font-bold">{gs.target + 1}</span></span>}
          </div>
          <div className="text-sm text-zinc-500">
            Innings {gs.innings} · {gs.bowling_team} bowling
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Field + controls */}
        <div className="lg:col-span-2 space-y-4">
          <CricketField
            fielders={fielders}
            onZoneClick={userBowling && gs.pending_action === "bowling_decision" ? toggleFielder : undefined}
            interactive={userBowling && gs.pending_action === "bowling_decision"}
            lastShotZone={gs.last_ball?.shot_zone}
            trajectory={
              gs.last_ball?.shot_zone
                ? { from: "pitch", to: gs.last_ball.shot_zone }
                : null
            }
          />

          {/* User controls */}
          {userTurn && (
            <div className="bg-zinc-900 rounded-xl p-4">
              {userBatting && gs.pending_action === "batting_decision" && (
                <BattingControls
                  currentMindset={currentMindset}
                  strikerName={strikerName}
                  onMindsetChange={(m) =>
                    sendAction("set_mindset", { player_id: gs.striker_id, mindset: m })
                  }
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
                />
              )}
            </div>
          )}

          {!userTurn && gs.status !== "completed" && (
            <div className="bg-zinc-900 rounded-xl p-4 text-center text-zinc-400 text-sm">
              {acting ? "Simulating…" : "AI is playing…"}
            </div>
          )}

          {/* Last ball result */}
          {gs.last_ball && (
            <div className="bg-zinc-900 rounded-xl p-4">
              <div className="text-xs text-zinc-500 uppercase tracking-wide mb-2">Last Ball</div>
              <div className="flex items-center gap-3">
                <span className={`text-2xl font-bold ${OUTCOME_COLORS[gs.last_ball.outcome] || "text-white"}`}>
                  {gs.last_ball.outcome === "wicket" ? "WICKET!" : gs.last_ball.outcome === "dot" ? "●" : gs.last_ball.outcome}
                </span>
                <div className="text-sm">
                  <span className="text-white">{gs.last_ball.striker}</span>
                  <span className="text-zinc-500"> vs </span>
                  <span className="text-white">{gs.last_ball.bowler}</span>
                </div>
                {gs.last_ball.delivery_type && (
                  <span className="text-xs text-zinc-500 ml-auto">{gs.last_ball.delivery_type}</span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          {/* Batting card */}
          <div className="bg-zinc-900 rounded-xl p-4">
            <div className="text-xs text-zinc-500 uppercase tracking-wide mb-3">Batting</div>
            <div className="space-y-2">
              {Object.values(gs.batting_card)
                .filter((l) => l.balls > 0 || l.player_id === gs.striker_id || l.player_id === gs.non_striker_id)
                .map((l) => (
                  <div key={l.player_id} className="text-xs flex items-center gap-2">
                    <div className="flex-1 text-zinc-300 truncate">
                      {l.player_name}
                      {l.player_id === gs.striker_id && <span className="text-emerald-400 ml-1">*</span>}
                      {l.player_id === gs.non_striker_id && l.player_id !== gs.striker_id && <span className="text-zinc-500 ml-1">°</span>}
                    </div>
                    <span className="text-white font-bold">{l.runs}</span>
                    <span className="text-zinc-500">({l.balls})</span>
                    {l.out && <span className="text-red-400">out</span>}
                  </div>
                ))}
            </div>
          </div>

          {/* Bowling card */}
          <div className="bg-zinc-900 rounded-xl p-4">
            <div className="text-xs text-zinc-500 uppercase tracking-wide mb-3">Bowling</div>
            <div className="space-y-2">
              {Object.values(gs.bowling_card).map((l) => (
                <div key={l.player_id} className="text-xs flex items-center gap-2">
                  <div className="flex-1 text-zinc-300 truncate">
                    {l.player_name}
                    {l.player_id === gs.current_bowler_id && <span className="text-blue-400 ml-1">▶</span>}
                  </div>
                  <span className="text-white">{l.wickets}-{l.runs_conceded}</span>
                  <span className="text-zinc-500">{formatOvers(l.balls || 0)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ball-by-ball feed */}
          <div className="bg-zinc-900 rounded-xl p-4">
            <div className="text-xs text-zinc-500 uppercase tracking-wide mb-3">Ball Feed</div>
            <div ref={feedRef} className="space-y-1 max-h-64 overflow-y-auto">
              {gs.events.slice(-30).map((e, i) => (
                <div key={i} className="text-xs flex items-center gap-2">
                  <span className="text-zinc-600 w-8 flex-shrink-0">{e.over}.{e.ball}</span>
                  <span className={`w-8 text-center font-bold ${OUTCOME_COLORS[e.outcome] || "text-white"}`}>
                    {e.outcome === "dot" ? "●" : e.outcome === "wicket" ? "W" : e.outcome}
                  </span>
                  <span className="text-zinc-400 truncate">{e.striker} v {e.bowler}</span>
                  <span className="text-zinc-600 ml-auto">{e.score_after}/{e.wickets_after}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Over summary */}
          {gs.over_summary.length > 0 && (
            <div className="bg-zinc-900 rounded-xl p-4">
              <div className="text-xs text-zinc-500 uppercase tracking-wide mb-2">Overs</div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {gs.over_summary.slice(-6).map((s, i) => (
                  <div key={i} className="text-xs text-zinc-400">{s}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-800 text-white px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
