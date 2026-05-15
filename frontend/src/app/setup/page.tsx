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

export default function SetupPage() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionId = params.get("session");
  const team1Name = params.get("team1") || "";
  const team2Name = params.get("team2") || "";
  const mode = params.get("mode") || "user_vs_ai";

  const [squad, setSquad] = useState<PlayerInfo[]>([]);
  const [lineup, setLineup] = useState<number[]>([]);
  const [captainId, setCaptainId] = useState<number | null>(null);
  const [wkId, setWkId] = useState<number | null>(null);
  const [ratings, setRatings] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const userTeam = team1Name;

  useEffect(() => {
    if (!userTeam) return;
    fetch(`${API}/teams`)
      .then((r) => r.json())
      .then(async (teams: TeamData[]) => {
        const team = teams.find((t) => t.name === userTeam);
        if (!team) return;
        setSquad(team.squad);

        // Load overalls for each player
        const overalls: Record<number, number> = {};
        await Promise.all(
          team.squad.map(async (p) => {
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

        // Auto-select first 11
        const first11 = team.squad.slice(0, 11).map((p) => p.id);
        setLineup(first11);
        setCaptainId(first11[0]);
        const wk = team.squad.find((p) => p.role === "wicket_keeper");
        setWkId(wk ? wk.id : first11[first11.length - 1]);
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
    if (lineup.length !== 11) {
      setError("Select exactly 11 players.");
      return;
    }
    if (!captainId || !wkId) {
      setError("Set captain and wicket-keeper.");
      return;
    }
    if (!sessionId) {
      setError("No session found.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API}/game/${sessionId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "set_lineup",
          payload: {
            team: "team1",
            player_ids: lineup,
            captain_id: captainId,
            wk_id: wkId,
          },
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
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-white">
        Loading squad…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Select Your XI</h1>
      <p className="text-zinc-400 text-sm mb-4">
        {userTeam} — choose 11 players, set captain and WK
      </p>

      <div className="flex items-center gap-4 mb-4 text-sm">
        <span className="text-zinc-400">
          Selected: <span className={lineup.length === 11 ? "text-emerald-400 font-bold" : "text-yellow-400 font-bold"}>{lineup.length}/11</span>
        </span>
        {captainId && <span className="bg-yellow-600 text-black px-2 py-0.5 rounded text-xs font-bold">C set</span>}
        {wkId && <span className="bg-purple-600 text-white px-2 py-0.5 rounded text-xs font-bold">WK set</span>}
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 mb-6">
        {squad.map((p) => (
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
          />
        ))}
      </div>

      {/* Batting order preview */}
      {lineup.length > 0 && (
        <div className="bg-zinc-900 rounded-xl p-4 mb-4">
          <div className="text-xs text-zinc-500 uppercase tracking-wide mb-3">Batting Order</div>
          <div className="space-y-1">
            {lineup.map((id, idx) => {
              const p = squad.find((s) => s.id === id);
              return (
                <div key={id} className="flex items-center gap-3 text-sm">
                  <span className="text-zinc-500 w-5 text-right">{idx + 1}.</span>
                  <span className="text-white font-medium">{p?.name}</span>
                  {captainId === id && <span className="text-xs bg-yellow-500 text-black px-1 rounded font-bold">C</span>}
                  {wkId === id && <span className="text-xs bg-purple-600 text-white px-1 rounded font-bold">WK</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={submitting || lineup.length !== 11 || !captainId || !wkId}
        className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl text-lg transition-all"
      >
        {submitting ? "Confirming…" : "Confirm Lineup →"}
      </button>
    </div>
  );
}
