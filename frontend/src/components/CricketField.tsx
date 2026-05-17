"use client";

import React from "react";

// Zones classified by proximity to batting crease
// OUTER = beyond the 30-yard circle (deep positions)
// INNER = within the 30-yard circle (close/mid positions)
export const OUTER_ZONES = new Set([
  "fine_leg", "deep_square_leg", "long_on", "long_off", "deep_cover", "third_man",
]);

const ZONE_POSITIONS: Record<string, [number, number]> = {
  // Inner ring
  slip:         [382, 172],
  gully:        [420, 202],
  point:        [460, 218],
  cover_point:  [448, 256],
  cover:        [412, 288],
  mid_off:      [318, 322],
  mid_on:       [280, 322],
  mid_wicket:   [196, 290],
  square_leg:   [164, 250],
  // Outer ring
  fine_leg:     [140, 222],
  deep_square_leg: [88, 276],
  long_on:      [215, 373],
  long_off:     [380, 373],
  deep_cover:   [462, 342],
  third_man:    [428, 158],
};

const ZONE_LABELS: Record<string, string> = {
  slip:           "Slip",
  gully:          "Gully",
  point:          "Point",
  cover_point:    "Cov Pt",
  cover:          "Cover",
  mid_off:        "Mid Off",
  mid_on:         "Mid On",
  mid_wicket:     "Mid Wkt",
  square_leg:     "Sq Leg",
  fine_leg:       "Fine Leg",
  deep_square_leg:"Dp Sq Leg",
  long_on:        "Long On",
  long_off:       "Long Off",
  deep_cover:     "Dp Cover",
  third_man:      "3rd Man",
};

interface CricketFieldProps {
  fielders?: string[];
  onZoneClick?: (zone: string) => void;
  trajectory?: { from: string; to: string } | null;
  interactive?: boolean;
  lastShotZone?: string;
  isPowerplay?: boolean;
  phase?: "powerplay" | "middle" | "death";
}

export default function CricketField({
  fielders = [],
  onZoneClick,
  trajectory,
  interactive = false,
  lastShotZone,
  isPowerplay = false,
  phase,
}: CricketFieldProps) {
  const fieldSet     = new Set(fielders);
  const outerFielders = fielders.filter((z) => OUTER_ZONES.has(z));
  const maxOuter      = isPowerplay ? 2 : 5;
  const outerFull     = outerFielders.length >= maxOuter;

  const traj = (() => {
    if (!trajectory?.to) return null;
    const to = ZONE_POSITIONS[trajectory.to];
    if (!to) return null;
    return { x1: 300, y1: 210, x2: to[0], y2: to[1] };
  })();

  const handleClick = (zone: string) => {
    if (!interactive || !onZoneClick) return;
    if (OUTER_ZONES.has(zone) && !fieldSet.has(zone) && outerFull) return;
    onZoneClick(zone);
  };

  const phaseColor = phase === "powerplay" ? "#34d399" : phase === "death" ? "#f87171" : "#fbbf24";
  const phaseLabel = phase === "powerplay" ? "⚡ POWERPLAY" : phase === "death" ? "🔥 DEATH" : "⚾ MIDDLE";

  return (
    <div style={{ userSelect: "none" }}>
      {/* Header bar when interactive */}
      {interactive && (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 8, padding: "0 2px", fontSize: 11,
        }}>
          <span style={{ color: "var(--muted)" }}>
            Click zones to place fielders · <span style={{ color: "var(--ink)" }}>Fielders: {fielders.length}</span>
          </span>
          <span>
            <span style={{ color: "var(--muted)" }}>Deep: </span>
            <span style={{
              fontWeight: 700,
              color: outerFull ? "#f87171" : "#34d399",
            }}>
              {outerFielders.length}/{maxOuter}
            </span>
            {isPowerplay && (
              <span style={{ color: "#f59e0b", marginLeft: 8, fontWeight: 600 }}>Powerplay limit</span>
            )}
          </span>
        </div>
      )}

      <svg
        viewBox="0 0 600 430"
        style={{ width: "100%", display: "block" }}
      >
        <defs>
          <radialGradient id="fgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#2d6b1a" />
            <stop offset="65%"  stopColor="#255815" />
            <stop offset="100%" stopColor="#173a0d" />
          </radialGradient>
          <radialGradient id="fgGrad2" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#326e1e" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#1a4510" stopOpacity="0" />
          </radialGradient>
          <marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#ffdd00" opacity="0.95" />
          </marker>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Ground base */}
        <ellipse cx="300" cy="220" rx="285" ry="204" fill="url(#fgGrad)" />
        {/* Mowing pattern overlay */}
        <ellipse cx="300" cy="220" rx="285" ry="204" fill="url(#fgGrad2)" />
        {/* Ground border */}
        <ellipse cx="300" cy="220" rx="285" ry="204" fill="none" stroke="#1a5010" strokeWidth="3" />
        {/* Boundary rope */}
        <ellipse cx="300" cy="220" rx="278" ry="197" fill="none" stroke="#fffde0" strokeWidth="1.5" opacity="0.35" strokeDasharray="none" />

        {/* 30-yard fielding circle */}
        <ellipse cx="300" cy="220" rx="152" ry="122"
          fill="none" stroke="#66cc44" strokeWidth="1.5"
          strokeDasharray="10 6" opacity="0.55" />

        {/* Pitch */}
        <rect x="287" y="168" width="26" height="104" rx="3" fill="#d4b56a" stroke="#b89045" strokeWidth="1.5" />
        {/* Pitch grain */}
        {[175, 183, 191, 199, 207, 215, 223, 231, 239, 247, 255, 263].map((y) => (
          <line key={y} x1={288} y1={y} x2={312} y2={y} stroke="#c09840" strokeWidth="0.6" opacity="0.45" />
        ))}

        {/* Stumps — top (bowler's end) */}
        <line x1="295" y1="165" x2="295" y2="173" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        <line x1="300" y1="165" x2="300" y2="173" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        <line x1="305" y1="165" x2="305" y2="173" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        {/* Bails */}
        <line x1="294" y1="166" x2="306" y2="166" stroke="#f0e0a0" strokeWidth="1.2" />

        {/* Stumps — bottom (batter's end) */}
        <line x1="295" y1="268" x2="295" y2="276" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        <line x1="300" y1="268" x2="300" y2="276" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        <line x1="305" y1="268" x2="305" y2="276" stroke="#f0e0a0" strokeWidth="2.2" strokeLinecap="round" />
        <line x1="294" y1="275" x2="306" y2="275" stroke="#f0e0a0" strokeWidth="1.2" />

        {/* Crease lines */}
        <line x1="281" y1="178" x2="319" y2="178" stroke="#fff" strokeWidth="1.8" opacity="0.65" />
        <line x1="281" y1="263" x2="319" y2="263" stroke="#fff" strokeWidth="1.8" opacity="0.65" />

        {/* Ball trajectory */}
        {traj && (
          <line
            x1={traj.x1} y1={traj.y1}
            x2={traj.x2} y2={traj.y2}
            stroke="#ffdd00" strokeWidth="2.5"
            strokeDasharray="9 5" opacity="0.9"
            markerEnd="url(#arrow)"
          />
        )}

        {/* Field zones */}
        {Object.entries(ZONE_POSITIONS).map(([zone, [x, y]]) => {
          const isFielder  = fieldSet.has(zone);
          const isLastShot = zone === lastShotZone;
          const isOuter    = OUTER_ZONES.has(zone);
          const isBlocked  = interactive && isOuter && !isFielder && outerFull;
          const isClickable = interactive && !!onZoneClick;

          let fill = "none", stroke = "#2266bb", strokeW = 1, opacity = 0.5;
          if (isLastShot)    { fill = "#ff6b35"; stroke = "#ff8855"; strokeW = 2; opacity = 1; }
          else if (isFielder){ fill = "#f0df18"; stroke = "#fff";    strokeW = 2.5; opacity = 1; }
          else if (isBlocked){ fill = "#4a1515"; stroke = "#661111"; opacity = 0.4; }
          else if (isClickable) {
            fill = isOuter ? "#2a3d70" : "#1e3d60";
            stroke = isOuter ? "#3355aa" : "#2255aa";
            opacity = 0.7;
          } else {
            fill = "#1a2d50";
            opacity = 0.45;
          }

          return (
            <g
              key={zone}
              onClick={() => handleClick(zone)}
              style={{ cursor: isClickable && !isBlocked ? "pointer" : "default" }}
            >
              {/* Hover ring for interactive zones */}
              {isClickable && !isBlocked && !isFielder && (
                <circle cx={x} cy={y} r={16} fill="transparent" stroke="transparent" />
              )}
              <circle
                cx={x} cy={y}
                r={isFielder ? 13 : isLastShot ? 12 : 11}
                fill={fill}
                stroke={stroke}
                strokeWidth={strokeW}
                opacity={opacity}
              />
              {/* Fielder dot */}
              {isFielder && (
                <circle cx={x} cy={y} r={4} fill="#1a1a00" opacity={0.7} />
              )}
              {/* Zone label */}
              <text
                x={x}
                y={y + (isFielder ? 24 : 21)}
                fontSize={isFielder ? "9.5" : "8"}
                fill={isFielder ? "#fff" : isBlocked ? "#664444" : "#7aabcc"}
                textAnchor="middle"
                fontFamily="'Space Grotesk', sans-serif"
                fontWeight={isFielder ? "700" : "500"}
                opacity={isFielder ? 1 : isBlocked ? 0.45 : 0.75}
              >
                {ZONE_LABELS[zone]}
              </text>
            </g>
          );
        })}

        {/* Wicket-keeper marker */}
        <circle cx="300" cy="192" r="8" fill="#3366aa" stroke="#6699cc" strokeWidth="1.5" opacity="0.85" />
        <text x="300" y="183" fontSize="8" fill="#88aacc" textAnchor="middle" fontFamily="sans-serif" opacity="0.75">WK</text>

        {/* Batter marker */}
        <circle cx="300" cy="234" r="9" fill="#e05c20" stroke="#fff" strokeWidth="2" />
        <text x="300" y="255" fontSize="8" fill="#aaa" textAnchor="middle" fontFamily="sans-serif">BAT</text>

        {/* Phase label overlay */}
        {phase && (
          <g>
            <rect x="8" y="8" width="90" height="22" rx="5" fill="rgba(0,0,0,0.55)" />
            <text x="14" y="23" fontSize="10" fontWeight="700" fill={phaseColor} fontFamily="sans-serif">
              {phaseLabel}
            </text>
          </g>
        )}
      </svg>

      {/* Fielder summary strip */}
      {fielders.length > 0 && (
        <div style={{
          display: "flex", gap: 12, justifyContent: "center",
          fontSize: 11, color: "var(--muted)", marginTop: 6,
        }}>
          <span>Total: <strong style={{ color: "var(--ink)" }}>{fielders.length}</strong></span>
          <span>·</span>
          <span>Deep: <strong style={{ color: outerFull ? "#f87171" : "var(--ink)" }}>{outerFielders.length}/{maxOuter}</strong></span>
          <span>·</span>
          <span>Close: <strong style={{ color: "var(--ink)" }}>{fielders.length - outerFielders.length}</strong></span>
        </div>
      )}
    </div>
  );
}
