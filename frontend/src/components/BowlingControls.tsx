"use client";

import React, { useState } from "react";

const LINES = [
  { key: "off_stump", label: "Off Stump",  icon: "→",  desc: "Outside off — edges, lbw" },
  { key: "middle",    label: "Middle",     icon: "↑",  desc: "Full of stumps — leg side danger" },
  { key: "leg_stump", label: "Leg Stump",  icon: "←",  desc: "On the pads — flicks/sweeps" },
  { key: "wide",      label: "Wide",       icon: "⇒",  desc: "Away from batter — dots/wides" },
] as const;

const LENGTHS = [
  { key: "full",         label: "Full",         icon: "▼",  desc: "Drive zone — lbw/yorker" },
  { key: "good_length",  label: "Good Length",  icon: "◆",  desc: "Best length — awkward bounce" },
  { key: "short",        label: "Short",        icon: "▲",  desc: "Back of a length — pull/cut" },
  { key: "bouncer",      label: "Bouncer",      icon: "⬆",  desc: "Head high — unsettle batter" },
] as const;

const AGGRESSIONS = [
  { key: "defensive", label: "Defensive", color: "#3b82f6", desc: "Keep it tight — dots over wickets" },
  { key: "normal",    label: "Normal",    color: "#8b5cf6", desc: "Balanced — wickets + economy" },
  { key: "attacking", label: "Attacking", color: "#ef4444", desc: "Go for wickets — boundary risk" },
] as const;

type Line       = (typeof LINES)[number]["key"];
type Length     = (typeof LENGTHS)[number]["key"];
type Aggression = (typeof AGGRESSIONS)[number]["key"];

// Pitch diagram coords: x = line (right=off_stump, left=leg), y = length (bottom=full, top=bouncer)
const PITCH_X: Record<Line, number>   = { wide: 38, off_stump: 29, middle: 20, leg_stump: 11 };
const PITCH_Y: Record<Length, number> = { full: 95, good_length: 70, short: 42, bouncer: 16 };

interface BowlingControlsProps {
  bowlerName: string;
  fielders: string[];
  onBowl: (opts: { line: Line; length: Length; aggression: Aggression; field_placement: string[] }) => void;
  disabled?: boolean;
  isPowerplay?: boolean;
}

export default function BowlingControls({
  bowlerName,
  fielders,
  onBowl,
  disabled = false,
  isPowerplay = false,
}: BowlingControlsProps) {
  const [line,       setLine]       = useState<Line>("off_stump");
  const [length,     setLength]     = useState<Length>("good_length");
  const [aggression, setAggression] = useState<Aggression>("normal");

  const lineInfo   = LINES.find((l) => l.key === line)!;
  const lengthInfo = LENGTHS.find((l) => l.key === length)!;
  const aggrInfo   = AGGRESSIONS.find((a) => a.key === aggression)!;

  const px = PITCH_X[line];
  const py = PITCH_Y[length];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Bowler name */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 18 }}>🎳</span>
        <div>
          <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Bowling</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)" }}>{bowlerName}</div>
        </div>
        {isPowerplay && (
          <span style={{
            marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "3px 8px",
            background: "rgba(52,211,153,0.15)", color: "#34d399", borderRadius: 999,
            border: "1px solid rgba(52,211,153,0.3)",
          }}>
            ⚡ POWERPLAY
          </span>
        )}
      </div>

      {/* Main controls + pitch diagram side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 14, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Line */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 6 }}>
              Line
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 5 }}>
              {LINES.map((l) => (
                <button
                  key={l.key}
                  type="button"
                  onClick={() => setLine(l.key)}
                  title={l.desc}
                  style={{
                    width: "100%",
                    padding: "7px 4px",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 8,
                    background: line === l.key ? "rgba(59,130,246,0.25)" : "rgba(255,255,255,0.04)",
                    border: `1.5px solid ${line === l.key ? "#3b82f6" : "var(--line)"}`,
                    color: line === l.key ? "#93c5fd" : "var(--muted)",
                    transform: "none",
                    cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, opacity: 0.8 }}>
              {lineInfo.desc}
            </div>
          </div>

          {/* Length */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 6 }}>
              Length
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 5 }}>
              {LENGTHS.map((l) => (
                <button
                  key={l.key}
                  type="button"
                  onClick={() => setLength(l.key)}
                  title={l.desc}
                  style={{
                    width: "100%",
                    padding: "7px 4px",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 8,
                    background: length === l.key ? "rgba(16,185,129,0.2)" : "rgba(255,255,255,0.04)",
                    border: `1.5px solid ${length === l.key ? "#10b981" : "var(--line)"}`,
                    color: length === l.key ? "#6ee7b7" : "var(--muted)",
                    transform: "none",
                    cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, opacity: 0.8 }}>
              {lengthInfo.desc}
            </div>
          </div>

          {/* Aggression */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", marginBottom: 6 }}>
              Aggression
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 5 }}>
              {AGGRESSIONS.map((a) => (
                <button
                  key={a.key}
                  type="button"
                  onClick={() => setAggression(a.key)}
                  style={{
                    width: "100%",
                    padding: "7px 4px",
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 8,
                    background: aggression === a.key ? `${a.color}28` : "rgba(255,255,255,0.04)",
                    border: `1.5px solid ${aggression === a.key ? a.color : "var(--line)"}`,
                    color: aggression === a.key ? a.color : "var(--muted)",
                    transform: "none",
                    cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                >
                  {a.label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, opacity: 0.8 }}>
              {aggrInfo.desc}
            </div>
          </div>
        </div>

        {/* Pitch diagram */}
        <div style={{ width: 60 }}>
          <div style={{ fontSize: 9, color: "var(--muted)", textAlign: "center", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Pitch
          </div>
          <svg viewBox="0 0 50 116" style={{ width: 60, display: "block", margin: "0 auto" }}>
            {/* Pitch surface */}
            <rect x="4" y="4" width="42" height="108" rx="3" fill="#c8a96e" stroke="#a07840" strokeWidth="1.5" />
            {/* Grain lines */}
            {[10, 18, 26, 34, 42, 50, 58, 66, 74, 82, 90, 98].map((y) => (
              <line key={y} x1={5} y1={y} x2={45} y2={y} stroke="#b89050" strokeWidth="0.5" opacity="0.5" />
            ))}
            {/* Stumps top */}
            <line x1="19" y1="4" x2="19" y2="10" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            <line x1="25" y1="4" x2="25" y2="10" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            <line x1="31" y1="4" x2="31" y2="10" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            {/* Stumps bottom */}
            <line x1="19" y1="106" x2="19" y2="112" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            <line x1="25" y1="106" x2="25" y2="112" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            <line x1="31" y1="106" x2="31" y2="112" stroke="#f0e0a0" strokeWidth="2" strokeLinecap="round" />
            {/* Crease lines */}
            <line x1="8"  y1="14" x2="42" y2="14" stroke="#fff" strokeWidth="1.5" opacity="0.6" />
            <line x1="8"  y1="102" x2="42" y2="102" stroke="#fff" strokeWidth="1.5" opacity="0.6" />
            {/* Delivery landing spot */}
            <circle
              cx={px} cy={py} r="5"
              fill="#ffdd00" opacity="0.9"
              style={{ filter: "drop-shadow(0 0 4px #ffdd00)" }}
            />
            <circle cx={px} cy={py} r="8" fill="none" stroke="#ffdd00" strokeWidth="1" opacity="0.45" />
            {/* Zone labels */}
            <text x="25" y="118" fontSize="6.5" fill="#8bbddd" textAnchor="middle" fontFamily="sans-serif">
              {`${lineInfo.label} · ${lengthInfo.label}`}
            </text>
          </svg>
        </div>
      </div>

      {/* Fielder count */}
      <div style={{
        padding: "8px 12px",
        background: "rgba(255,255,255,0.03)",
        borderRadius: 8,
        border: "1px solid var(--line)",
        fontSize: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <span style={{ color: "var(--muted)" }}>
          🟡 Fielders placed: <strong style={{ color: fielders.length > 0 ? "var(--ink)" : "var(--muted)" }}>{fielders.length}</strong>
          <span style={{ color: "var(--muted)", fontSize: 10, marginLeft: 6 }}>
            (click field zones to place)
          </span>
        </span>
        {isPowerplay && (
          <span style={{ color: "#f59e0b", fontSize: 11, fontWeight: 600 }}>
            Max 2 deep
          </span>
        )}
      </div>

      {/* Bowl button */}
      <button
        type="button"
        onClick={() => !disabled && onBowl({ line, length, aggression, field_placement: fielders })}
        disabled={disabled}
        style={{
          width: "100%",
          padding: "14px",
          fontSize: 16,
          fontWeight: 700,
          borderRadius: 12,
          background: disabled ? "var(--bg-alt)" : "linear-gradient(90deg, #ea580c, #dc2626)",
          color: disabled ? "var(--muted)" : "#fff",
          border: "none",
          letterSpacing: "0.02em",
          transform: "none",
        }}
      >
        🎯 Bowl — {lineInfo.label} · {lengthInfo.label}
      </button>
    </div>
  );
}
