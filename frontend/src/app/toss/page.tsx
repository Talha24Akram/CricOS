"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export default function TossPage() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionId = params.get("session") || "";
  const team1 = params.get("team1") || "Team 1";
  const team2 = params.get("team2") || "Team 2";

  const [flipping, setFlipping] = useState(false);
  const [tossWinner, setTossWinner] = useState<string | null>(null);
  const [decision, setDecision] = useState<"bat" | "bowl" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const flipCoin = () => {
    if (flipping || tossWinner) return;
    setFlipping(true);
    setTimeout(() => {
      const winner = Math.random() < 0.5 ? team1 : team2;
      setTossWinner(winner);
      setFlipping(false);
    }, 1200);
  };

  const handleDecision = async (dec: "bat" | "bowl") => {
    if (!tossWinner || !sessionId) return;
    setDecision(dec);
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API}/game/${sessionId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "toss_decision",
          payload: { toss_winner: tossWinner, decision: dec },
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      router.push(`/game?session=${sessionId}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
      setSubmitting(false);
    }
  };

  const isUserTossWinner = tossWinner === team1;

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col items-center justify-center gap-8 p-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-1">Toss</h1>
        <p className="text-zinc-400">{team1} vs {team2}</p>
      </div>

      {/* Coin */}
      <button
        onClick={flipCoin}
        disabled={flipping || !!tossWinner}
        className={`
          w-32 h-32 rounded-full text-5xl font-bold transition-all select-none
          ${flipping ? "animate-spin bg-yellow-500" : ""}
          ${!tossWinner ? "bg-yellow-600 hover:bg-yellow-500 cursor-pointer shadow-lg" : "bg-yellow-600 cursor-default"}
          ${tossWinner ? "scale-110" : ""}
          flex items-center justify-center
        `}
        style={{ animationDuration: "0.3s" }}
      >
        {flipping ? "🪙" : tossWinner ? "🏆" : "🪙"}
      </button>

      {!tossWinner && !flipping && (
        <p className="text-zinc-400 text-sm">Tap the coin to flip</p>
      )}

      {flipping && (
        <p className="text-yellow-400 font-medium animate-pulse">Flipping…</p>
      )}

      {tossWinner && (
        <div className="flex flex-col items-center gap-6 w-full max-w-sm">
          <div className="text-center">
            <p className="text-zinc-400 text-sm mb-1">Toss won by</p>
            <p className="text-2xl font-bold text-yellow-400">{tossWinner}</p>
          </div>

          {isUserTossWinner ? (
            <div className="w-full">
              <p className="text-zinc-300 text-center mb-4">What will you do?</p>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => handleDecision("bat")}
                  disabled={submitting}
                  className="py-4 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-bold text-lg transition-all disabled:opacity-40"
                >
                  🏏 Bat First
                </button>
                <button
                  onClick={() => handleDecision("bowl")}
                  disabled={submitting}
                  className="py-4 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold text-lg transition-all disabled:opacity-40"
                >
                  🎳 Bowl First
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full text-center">
              <p className="text-zinc-300 mb-4">
                {tossWinner} chose to{" "}
                <span className="text-yellow-400 font-bold">
                  {Math.random() < 0.6 ? "bat" : "bowl"} first
                </span>
              </p>
              <button
                onClick={() => handleDecision(Math.random() < 0.6 ? "bat" : "bowl")}
                disabled={submitting}
                className="w-full py-4 bg-zinc-600 hover:bg-zinc-500 rounded-xl font-bold transition-all disabled:opacity-40"
              >
                {submitting ? "Loading…" : "Continue →"}
              </button>
            </div>
          )}
        </div>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}
    </div>
  );
}
