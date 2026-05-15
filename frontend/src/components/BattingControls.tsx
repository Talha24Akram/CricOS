"use client";

import React from "react";

const MINDSETS = [
  { key: "ultra_defensive", label: "Ultra Def", emoji: "🛡️🛡️", desc: "Survive at all costs" },
  { key: "defensive", label: "Defensive", emoji: "🛡️", desc: "Play it safe" },
  { key: "balanced", label: "Balanced", emoji: "⚖️", desc: "Normal play" },
  { key: "aggressive", label: "Aggressive", emoji: "⚡", desc: "Attack the bowling" },
  { key: "ultra_aggressive", label: "Ultra Agg", emoji: "💥💥", desc: "Go for broke" },
] as const;

type Mindset = (typeof MINDSETS)[number]["key"];

interface BattingControlsProps {
  currentMindset: Mindset;
  strikerName: string;
  onMindsetChange: (m: Mindset) => void;
  onSimBall: () => void;
  onSimOver: () => void;
  disabled?: boolean;
}

export default function BattingControls({
  currentMindset,
  strikerName,
  onMindsetChange,
  onSimBall,
  onSimOver,
  disabled = false,
}: BattingControlsProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="text-sm text-zinc-400 font-medium">
        Batting: <span className="text-white font-bold">{strikerName}</span>
      </div>

      <div className="text-xs text-zinc-500 uppercase tracking-wide">Mindset</div>
      <div className="flex flex-wrap gap-2">
        {MINDSETS.map((m) => (
          <button
            key={m.key}
            onClick={() => !disabled && onMindsetChange(m.key)}
            title={m.desc}
            disabled={disabled}
            className={`
              px-3 py-2 rounded text-sm font-medium transition-all
              ${currentMindset === m.key
                ? "bg-emerald-600 text-white ring-2 ring-emerald-400"
                : "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"}
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
          >
            <span className="mr-1">{m.emoji}</span>
            {m.label}
          </button>
        ))}
      </div>

      <div className="flex gap-3 mt-1">
        <button
          onClick={onSimBall}
          disabled={disabled}
          className={`
            flex-1 py-3 rounded-lg text-base font-bold transition-all
            bg-emerald-600 hover:bg-emerald-500 text-white
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
        >
          ▶ Sim Ball
        </button>
        <button
          onClick={onSimOver}
          disabled={disabled}
          className={`
            flex-1 py-3 rounded-lg text-base font-semibold transition-all
            bg-zinc-600 hover:bg-zinc-500 text-white
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
        >
          ⏭ Sim Over
        </button>
      </div>
    </div>
  );
}
