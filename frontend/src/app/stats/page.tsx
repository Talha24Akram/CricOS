"use client";

import { useEffect, useState } from "react";

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

const TEAMS = ["India", "Pakistan", "Australia", "England", "New Zealand", "South Africa", "West Indies", "Sri Lanka"];

export default function StatsPage() {
  const [team, setTeam] = useState(TEAMS[0]);
  const [stats, setStats] = useState<PlayerStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"batting" | "bowling">("batting");

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/teams/${encodeURIComponent(team)}/stats`)
      .then((r) => r.json())
      .then((d) => setStats(Array.isArray(d) ? d : []))
      .finally(() => setLoading(false));
  }, [team]);

  const sorted =
    tab === "batting"
      ? [...stats].sort((a, b) => b.sim_batting.runs - a.sim_batting.runs)
      : [...stats].sort((a, b) => b.sim_bowling.wickets - a.sim_bowling.wickets);

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Player Stats</h1>

      {/* Team selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {TEAMS.map((t) => (
          <button
            key={t}
            onClick={() => setTeam(t)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
              ${team === t ? "bg-emerald-600 text-white" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setTab("batting")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${tab === "batting" ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-400 hover:bg-zinc-800"}`}
        >
          Batting
        </button>
        <button
          onClick={() => setTab("bowling")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${tab === "bowling" ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-400 hover:bg-zinc-800"}`}
        >
          Bowling
        </button>
      </div>

      {loading ? (
        <div className="text-zinc-500 text-sm">Loading…</div>
      ) : (
        <div className="bg-zinc-900 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-500 text-xs uppercase border-b border-zinc-800">
                <th className="text-left px-4 py-3">Player</th>
                {tab === "batting" ? (
                  <>
                    <th className="text-center px-3 py-3">M</th>
                    <th className="text-center px-3 py-3">Runs</th>
                    <th className="text-center px-3 py-3">Avg</th>
                    <th className="text-center px-3 py-3">SR</th>
                    <th className="text-center px-3 py-3">4s</th>
                    <th className="text-center px-3 py-3">6s</th>
                  </>
                ) : (
                  <>
                    <th className="text-center px-3 py-3">M</th>
                    <th className="text-center px-3 py-3">Wkts</th>
                    <th className="text-center px-3 py-3">Avg</th>
                    <th className="text-center px-3 py-3">Econ</th>
                    <th className="text-center px-3 py-3">SR</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {sorted.map((p) => (
                <tr key={p.player_id} className="border-b border-zinc-800 hover:bg-zinc-800/50 transition-all">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full overflow-hidden bg-zinc-700 flex-shrink-0">
                        {p.photo_url ? (
                          <img src={p.photo_url} alt={p.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-xs">👤</div>
                        )}
                      </div>
                      <div>
                        <div className="font-medium text-white">{p.name}</div>
                        <div className="text-xs text-zinc-500">{p.role} · {p.overall}</div>
                      </div>
                    </div>
                  </td>
                  {tab === "batting" ? (
                    <>
                      <td className="text-center px-3 py-3 text-zinc-400">{p.sim_batting.matches}</td>
                      <td className="text-center px-3 py-3 text-white font-bold">{p.sim_batting.runs}</td>
                      <td className="text-center px-3 py-3 text-zinc-300">{p.sim_batting.average || "-"}</td>
                      <td className="text-center px-3 py-3 text-zinc-300">{p.sim_batting.strike_rate || "-"}</td>
                      <td className="text-center px-3 py-3 text-emerald-400">{p.sim_batting.fours}</td>
                      <td className="text-center px-3 py-3 text-yellow-400">{p.sim_batting.sixes}</td>
                    </>
                  ) : (
                    <>
                      <td className="text-center px-3 py-3 text-zinc-400">{p.sim_batting.matches}</td>
                      <td className="text-center px-3 py-3 text-white font-bold">{p.sim_bowling.wickets}</td>
                      <td className="text-center px-3 py-3 text-zinc-300">{p.sim_bowling.average || "-"}</td>
                      <td className="text-center px-3 py-3 text-zinc-300">{p.sim_bowling.economy || "-"}</td>
                      <td className="text-center px-3 py-3 text-zinc-300">{p.sim_bowling.strike_rate || "-"}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          {sorted.length === 0 && (
            <div className="text-center text-zinc-500 py-10">No matches played yet</div>
          )}
        </div>
      )}
    </div>
  );
}
