"use client";

import { useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

// Pick once and store — never call Math.random() twice for the same decision
function aiDecision(): "bat" | "bowl" {
  return Math.random() < 0.6 ? "bat" : "bowl";
}

export default function TossPage() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionId = params.get("session") || "";
  const team1 = params.get("team1") || "Team 1";
  const team2 = params.get("team2") || "Team 2";

  const [flipping,    setFlipping]    = useState(false);
  const [tossWinner,  setTossWinner]  = useState<string | null>(null);
  const [submitting,  setSubmitting]  = useState(false);
  const [error,       setError]       = useState("");

  // AI decision stored once when toss winner is determined
  const aiDecRef = useRef<"bat" | "bowl" | null>(null);

  const flipCoin = () => {
    if (flipping || tossWinner) return;
    setFlipping(true);
    setTimeout(() => {
      const winner = Math.random() < 0.5 ? team1 : team2;
      setTossWinner(winner);
      setFlipping(false);
      // Pre-compute AI decision right now if AI wins
      if (winner !== team1) {
        aiDecRef.current = aiDecision();
      }
    }, 1400);
  };

  const submitDecision = async (dec: "bat" | "bowl") => {
    if (!tossWinner || !sessionId) return;
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

  const userWon = tossWinner === team1;
  const aiDec   = aiDecRef.current;

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
      {/* Match header */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--muted)", marginBottom: 8 }}>
          The Toss
        </h2>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{team1}</span>
          <span style={{ color: "var(--muted)", fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: 3 }}>VS</span>
          <span style={{ fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{team2}</span>
        </div>
      </div>

      {/* Coin */}
      <div style={{ marginBottom: 32 }}>
        <button
          type="button"
          onClick={flipCoin}
          disabled={flipping || !!tossWinner}
          style={{
            width: 130,
            height: 130,
            borderRadius: "50%",
            fontSize: 52,
            border: "none",
            background: tossWinner
              ? "radial-gradient(circle, #b8860b, #8b6914)"
              : "radial-gradient(circle, #d4a017, #a07810)",
            boxShadow: tossWinner
              ? "0 0 40px rgba(212,160,23,0.5), 0 0 0 4px rgba(212,160,23,0.2)"
              : "0 6px 30px rgba(212,160,23,0.35)",
            cursor: tossWinner ? "default" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto",
            transition: "all 0.15s",
            animation: flipping ? "spin 0.25s linear infinite" : tossWinner ? "pop 0.3s ease" : "none",
            transform: "none",
          }}
        >
          {flipping ? "🪙" : tossWinner ? "🏆" : "🪙"}
        </button>

        <style>{`
          @keyframes spin { to { transform: rotateY(360deg); } }
          @keyframes pop  { 0% { transform: scale(0.85); } 60% { transform: scale(1.12); } 100% { transform: scale(1); } }
        `}</style>

        <div style={{ marginTop: 14, fontSize: 14, color: "var(--muted)", minHeight: 24 }}>
          {flipping    && <span style={{ color: "#f59e0b", fontWeight: 600 }}>Flipping…</span>}
          {!tossWinner && !flipping && "Tap the coin to flip"}
        </div>
      </div>

      {/* Result */}
      {tossWinner && (
        <div className="card" style={{ animation: "fadeIn 0.3s ease" }}>
          <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }`}</style>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Toss won by
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#f59e0b" }}>{tossWinner}</div>
          </div>

          {userWon ? (
            <>
              <div style={{ fontSize: 14, color: "var(--muted)", marginBottom: 16 }}>
                Congratulations! What will you do?
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <button
                  type="button"
                  onClick={() => submitDecision("bat")}
                  disabled={submitting}
                  style={{
                    width: "100%",
                    padding: "16px 12px",
                    fontSize: 15,
                    fontWeight: 700,
                    borderRadius: 12,
                    background: "linear-gradient(135deg, #059669, #047857)",
                    color: "#fff",
                    border: "none",
                    transform: "none",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span style={{ fontSize: 28 }}>🏏</span>
                  <span>Bat First</span>
                  <span style={{ fontSize: 11, opacity: 0.7, fontWeight: 400 }}>Set a target</span>
                </button>
                <button
                  type="button"
                  onClick={() => submitDecision("bowl")}
                  disabled={submitting}
                  style={{
                    width: "100%",
                    padding: "16px 12px",
                    fontSize: 15,
                    fontWeight: 700,
                    borderRadius: 12,
                    background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                    color: "#fff",
                    border: "none",
                    transform: "none",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span style={{ fontSize: 28 }}>🎳</span>
                  <span>Bowl First</span>
                  <span style={{ fontSize: 11, opacity: 0.7, fontWeight: 400 }}>Chase the target</span>
                </button>
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 14, color: "var(--muted)", marginBottom: 6 }}>
                {tossWinner} chose to{" "}
                <strong style={{ color: aiDec === "bat" ? "#34d399" : "#60a5fa" }}>
                  {aiDec === "bat" ? "bat" : "bowl"} first
                </strong>
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 20, opacity: 0.7 }}>
                {aiDec === "bat"
                  ? "They'll look to post a big total for you to chase."
                  : "They'll look to restrict you early and defend."}
              </div>
              <button
                type="button"
                onClick={() => submitDecision(aiDec!)}
                disabled={submitting || !aiDec}
                style={{
                  width: "100%",
                  padding: "14px",
                  fontSize: 15,
                  fontWeight: 700,
                  borderRadius: 12,
                  background: "linear-gradient(90deg, var(--accent), #17b9ff)",
                  color: "#041018",
                  border: "none",
                  transform: "none",
                }}
              >
                {submitting ? "Loading match…" : "Continue to Match →"}
              </button>
            </>
          )}
        </div>
      )}

      {error && (
        <div style={{ marginTop: 16, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "10px 14px", color: "#f87171", fontSize: 13 }}>
          {error}
        </div>
      )}
    </div>
  );
}
