"use client";

import { useEffect, useMemo, useState } from "react";

import { ScoreGraph } from "@/components/ScoreGraph";
import { apiPost } from "@/lib/api";

type Ball = {
  innings: number;
  over: number;
  ball: number;
  striker: string;
  bowler: string;
  outcome: string;
  runs: number;
  score: string;
};

export default function LivePage() {
  const [data, setData] = useState<any>(null);
  const [tone, setTone] = useState("normal");
  const [commentary, setCommentary] = useState<Record<string, string>>({});

  useEffect(() => {
    const raw = localStorage.getItem("cricketos:lastSimulation");
    if (raw) setData(JSON.parse(raw));
  }, []);

  const points = useMemo(() => {
    const balls: Ball[] = data?.ball_by_ball || [];
    return balls.map((b, idx) => ({
      ball: `${b.innings}.${b.over}.${b.ball}`,
      score: Number((balls[idx]?.score || "0/0").split("/")[0]),
    }));
  }, [data]);

  async function generateCommentary(ball: Ball) {
    const key = `${ball.innings}-${ball.over}-${ball.ball}`;
    if (commentary[key]) return;
    const line = await apiPost<{ commentary: string }>("/commentary", {
      tone,
      match_state: {
        batter: ball.striker,
        bowler: ball.bowler,
        delivery: "auto",
        outcome: ball.outcome,
        score: ball.score,
        over: `${ball.over}.${ball.ball}`,
      },
    });
    setCommentary((prev) => ({ ...prev, [key]: line.commentary }));
  }

  if (!data) {
    return <div className="card">Run a simulation from Home first.</div>;
  }

  const balls: Ball[] = data.ball_by_ball || [];

  return (
    <section className="grid" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
      <div className="grid">
        <div className="card">
          <h2 style={{ fontSize: 30 }}>{data.innings[0].team} vs {data.innings[1].team}</h2>
          <p>{data.winner} won by {data.margin}</p>
        </div>
        <ScoreGraph points={points} />
      </div>

      <div className="card" style={{ maxHeight: 620, overflow: "auto" }}>
        <h3>Live Feed</h3>
        <label>Commentary Tone</label>
        <select value={tone} onChange={(e) => setTone(e.target.value)}>
          <option value="normal">Normal</option>
          <option value="hype">Hype</option>
          <option value="meme">Meme</option>
        </select>
        {balls.slice(0, 60).map((ball) => {
          const key = `${ball.innings}-${ball.over}-${ball.ball}`;
          return (
            <div key={key} className="card" style={{ marginTop: 10 }}>
              <strong>{ball.over}.{ball.ball} - {ball.striker} vs {ball.bowler}</strong>
              <div>{ball.outcome.toUpperCase()} | {ball.score}</div>
              <button onClick={() => generateCommentary(ball)} style={{ marginTop: 8 }}>Generate Commentary</button>
              {commentary[key] && <p>{commentary[key]}</p>}
            </div>
          );
        })}
      </div>
    </section>
  );
}
