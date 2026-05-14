"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { RadarRatings } from "@/components/RadarRatings";
import { apiGet } from "@/lib/api";

export default function PlayerProfilePage() {
  const params = useParams<{ id: string }>();
  const [player, setPlayer] = useState<any>(null);

  useEffect(() => {
    if (!params?.id) return;
    apiGet(`/players/${params.id}`).then(setPlayer).catch(() => setPlayer(null));
  }, [params?.id]);

  if (!player) return <div className="card">Player not found or ratings unavailable.</div>;

  return (
    <section className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
      <article className="card">
        <h2 style={{ fontSize: 34 }}>{player.name}</h2>
        <p>Batting Style: {player.batting_style || "Unknown"}</p>
        <p>Bowling Style: {player.bowling_style || "Unknown"}</p>
        <p>Arm: {player.arm || "Unknown"}</p>
      </article>
      <RadarRatings ratings={player.ratings || {}} />
    </section>
  );
}
