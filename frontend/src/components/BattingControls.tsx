"use client";

import React from "react";

const MINDSETS = [
  {
    key:   "ultra_defensive",
    label: "Ultra Defensive",
    short: "Ultra Def",
    emoji: "🛡️",
    desc:  "Block everything. Survive at all costs.",
    risk:  1,
    color: "#3b82f6",
  },
  {
    key:   "defensive",
    label: "Defensive",
    short: "Defensive",
    emoji: "🔒",
    desc:  "Play safe. Dot balls over boundaries.",
    risk:  2,
    color: "#0ea5e9",
  },
  {
    key:   "balanced",
    label: "Balanced",
    short: "Balanced",
    emoji: "⚖️",
    desc:  "Normal play. Trust your instincts.",
    risk:  3,
    color: "#8b5cf6",
  },
  {
    key:   "aggressive",
    label: "Aggressive",
    short: "Aggressive",
    emoji: "⚡",
    desc:  "Look for boundaries. Higher wicket risk.",
    risk:  4,
    color: "#f59e0b",
  },
  {
    key:   "ultra_aggressive",
    label: "Ultra Aggressive",
    short: "Ultra Agg",
    emoji: "💥",
    desc:  "Go for broke. Every ball is a scoring chance.",
    risk:  5,
    color: "#ef4444",
  },
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
  const active = MINDSETS.find((m) => m.key === currentMindset)!;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Striker label */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 18 }}>🏏</span>
        <div>
          <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>On Strike</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)" }}>{strikerName}</div>
        </div>
        <div style={{
          marginLeft: "auto",
          padding: "4px 10px",
          borderRadius: 999,
          background: `${active.color}22`,
          border: `1px solid ${active.color}55`,
          fontSize: 12,
          fontWeight: 700,
          color: active.color,
        }}>
          {active.emoji} {active.short}
        </div>
      </div>

      {/* Active mindset description */}
      <div style={{
        padding: "8px 12px",
        background: `${active.color}12`,
        borderLeft: `3px solid ${active.color}`,
        borderRadius: "0 8px 8px 0",
        fontSize: 12,
        color: "var(--muted)",
      }}>
        {active.desc}
      </div>

      {/* Risk bar */}
      <div>
        <div style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
          Mindset
        </div>
        <div style={{ display: "flex", gap: 5 }}>
          {MINDSETS.map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => !disabled && onMindsetChange(m.key)}
              disabled={disabled}
              title={m.desc}
              style={{
                flex: 1,
                padding: "8px 2px",
                borderRadius: 8,
                background: currentMindset === m.key ? `${m.color}30` : "rgba(255,255,255,0.04)",
                border: `2px solid ${currentMindset === m.key ? m.color : "var(--line)"}`,
                color: currentMindset === m.key ? m.color : "var(--muted)",
                fontSize: 11,
                fontWeight: currentMindset === m.key ? 700 : 500,
                cursor: disabled ? "not-allowed" : "pointer",
                transform: "none",
                transition: "all 0.12s",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
              }}
            >
              <span style={{ fontSize: 16 }}>{m.emoji}</span>
              <span style={{ fontSize: 9, lineHeight: 1.2, textAlign: "center" }}>{m.short}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Risk / reward indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 10, color: "var(--muted)", minWidth: 60 }}>Risk / Reward</span>
        <div style={{ flex: 1, height: 6, background: "var(--line)", borderRadius: 999, overflow: "hidden" }}>
          <div style={{
            width: `${(active.risk / 5) * 100}%`,
            height: "100%",
            background: `linear-gradient(90deg, #3b82f6, ${active.color})`,
            borderRadius: 999,
            transition: "width 0.25s ease",
          }} />
        </div>
        <span style={{ fontSize: 10, color: active.color, fontWeight: 700, minWidth: 30, textAlign: "right" }}>
          {active.risk}/5
        </span>
      </div>

      {/* Action buttons */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 8, marginTop: 2 }}>
        <button
          type="button"
          onClick={onSimBall}
          disabled={disabled}
          style={{
            width: "100%",
            padding: "13px",
            fontSize: 15,
            fontWeight: 700,
            borderRadius: 12,
            background: disabled ? "var(--bg-alt)" : `linear-gradient(90deg, ${active.color}, ${active.color}bb)`,
            color: disabled ? "var(--muted)" : "#fff",
            border: "none",
            transform: "none",
            letterSpacing: "0.02em",
          }}
        >
          ▶ Sim Ball
        </button>
        <button
          type="button"
          onClick={onSimOver}
          disabled={disabled}
          style={{
            width: "100%",
            padding: "13px",
            fontSize: 13,
            fontWeight: 600,
            borderRadius: 12,
            background: "rgba(255,255,255,0.06)",
            color: disabled ? "var(--muted)" : "var(--muted)",
            border: "1px solid var(--line)",
            transform: "none",
          }}
        >
          ⏭ Full Over
        </button>
      </div>
    </div>
  );
}
