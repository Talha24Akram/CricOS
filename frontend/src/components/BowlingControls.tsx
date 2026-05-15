"use client";

import React, { useState } from "react";

const LINES = [
  { key: "off_stump", label: "Off Stump" },
  { key: "middle", label: "Middle" },
  { key: "leg_stump", label: "Leg Stump" },
  { key: "wide", label: "Wide" },
] as const;

const LENGTHS = [
  { key: "full", label: "Full" },
  { key: "good_length", label: "Good Length" },
  { key: "short", label: "Short" },
  { key: "bouncer", label: "Bouncer" },
] as const;

const AGGRESSIONS = [
  { key: "defensive", label: "🛡 Defensive" },
  { key: "normal", label: "⚖ Normal" },
  { key: "attacking", label: "⚔ Attacking" },
] as const;

type Line = (typeof LINES)[number]["key"];
type Length = (typeof LENGTHS)[number]["key"];
type Aggression = (typeof AGGRESSIONS)[number]["key"];

interface BowlingControlsProps {
  bowlerName: string;
  fielders: string[];
  onBowl: (opts: { line: Line; length: Length; aggression: Aggression; field_placement: string[] }) => void;
  disabled?: boolean;
}

export default function BowlingControls({ bowlerName, fielders, onBowl, disabled = false }: BowlingControlsProps) {
  const [line, setLine] = useState<Line>("off_stump");
  const [length, setLength] = useState<Length>("good_length");
  const [aggression, setAggression] = useState<Aggression>("normal");

  const handleBowl = () => {
    if (!disabled) {
      onBowl({ line, length, aggression, field_placement: fielders });
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="text-sm text-zinc-400 font-medium">
        Bowling: <span className="text-white font-bold">{bowlerName}</span>
      </div>

      <div>
        <div className="text-xs text-zinc-500 uppercase tracking-wide mb-2">Line</div>
        <div className="grid grid-cols-4 gap-1">
          {LINES.map((l) => (
            <button
              key={l.key}
              onClick={() => setLine(l.key)}
              className={`py-2 rounded text-xs font-medium transition-all
                ${line === l.key ? "bg-blue-600 text-white" : "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="text-xs text-zinc-500 uppercase tracking-wide mb-2">Length</div>
        <div className="grid grid-cols-4 gap-1">
          {LENGTHS.map((l) => (
            <button
              key={l.key}
              onClick={() => setLength(l.key)}
              className={`py-2 rounded text-xs font-medium transition-all
                ${length === l.key ? "bg-blue-600 text-white" : "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="text-xs text-zinc-500 uppercase tracking-wide mb-2">Aggression</div>
        <div className="grid grid-cols-3 gap-1">
          {AGGRESSIONS.map((a) => (
            <button
              key={a.key}
              onClick={() => setAggression(a.key)}
              className={`py-2 rounded text-xs font-medium transition-all
                ${aggression === a.key ? "bg-orange-600 text-white" : "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"}`}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <div className="text-xs text-zinc-500">
        Fielders set: <span className="text-zinc-300">{fielders.length}</span> — click zones on field to toggle
      </div>

      <button
        onClick={handleBowl}
        disabled={disabled}
        className={`
          w-full py-3 rounded-lg text-base font-bold transition-all mt-1
          bg-orange-600 hover:bg-orange-500 text-white
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        🎯 Bowl
      </button>
    </div>
  );
}
