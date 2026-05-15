"use client";

import React from "react";

const ZONE_POSITIONS: Record<string, [number, number]> = {
  slip: [385, 178],
  gully: [422, 208],
  point: [468, 222],
  cover_point: [452, 258],
  cover: [415, 290],
  mid_off: [318, 325],
  mid_on: [278, 325],
  mid_wicket: [198, 292],
  square_leg: [168, 252],
  fine_leg: [148, 228],
  deep_square_leg: [95, 282],
  long_on: [218, 372],
  long_off: [375, 372],
  deep_cover: [462, 342],
  third_man: [425, 162],
};

const ZONE_LABELS: Record<string, string> = {
  slip: "Slip",
  gully: "Gully",
  point: "Point",
  cover_point: "Cov Pt",
  cover: "Cover",
  mid_off: "Mid Off",
  mid_on: "Mid On",
  mid_wicket: "Mid Wkt",
  square_leg: "Sq Leg",
  fine_leg: "Fine Leg",
  deep_square_leg: "Dp Sq Leg",
  long_on: "Long On",
  long_off: "Long Off",
  deep_cover: "Dp Cover",
  third_man: "3rd Man",
};

interface CricketFieldProps {
  fielders?: string[];
  onZoneClick?: (zone: string) => void;
  trajectory?: { from: string; to: string } | null;
  interactive?: boolean;
  lastShotZone?: string;
}

export default function CricketField({
  fielders = [],
  onZoneClick,
  trajectory,
  interactive = false,
  lastShotZone,
}: CricketFieldProps) {
  const fieldSet = new Set(fielders);

  const getTrajectoryPoints = () => {
    if (!trajectory) return null;
    const from = trajectory.from ? ZONE_POSITIONS[trajectory.from] : [300, 230];
    const to = trajectory.to ? ZONE_POSITIONS[trajectory.to] : null;
    if (!from || !to) return null;
    return { x1: 300, y1: 210, x2: to[0], y2: to[1] };
  };

  const traj = getTrajectoryPoints();

  return (
    <svg
      viewBox="0 0 600 420"
      className="w-full max-w-lg mx-auto select-none"
      style={{ background: "#2d5a1b" }}
    >
      {/* Outfield */}
      <ellipse cx="300" cy="220" rx="280" ry="200" fill="#3a7a24" stroke="#4a9a34" strokeWidth="2" />
      {/* Infield circle */}
      <ellipse cx="300" cy="220" rx="150" ry="120" fill="none" stroke="#5aaa44" strokeWidth="1" strokeDasharray="6 4" opacity="0.6" />
      {/* Pitch */}
      <rect x="288" y="170" width="24" height="100" rx="2" fill="#c8a96e" stroke="#a08050" strokeWidth="1" />
      {/* Stumps */}
      <rect x="295" y="170" width="10" height="4" fill="#e0c080" />
      <rect x="295" y="266" width="10" height="4" fill="#e0c080" />
      {/* Crease lines */}
      <line x1="285" y1="178" x2="315" y2="178" stroke="#fff" strokeWidth="1.5" opacity="0.6" />
      <line x1="285" y1="262" x2="315" y2="262" stroke="#fff" strokeWidth="1.5" opacity="0.6" />

      {/* Ball trajectory */}
      {traj && (
        <line
          x1={traj.x1} y1={traj.y1}
          x2={traj.x2} y2={traj.y2}
          stroke="#ffdd00"
          strokeWidth="2.5"
          strokeDasharray="6 3"
          opacity="0.85"
          markerEnd="url(#arrow)"
        />
      )}
      <defs>
        <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#ffdd00" />
        </marker>
      </defs>

      {/* Field zones */}
      {Object.entries(ZONE_POSITIONS).map(([zone, [x, y]]) => {
        const isFielder = fieldSet.has(zone);
        const isLastShot = zone === lastShotZone;
        const isClickable = interactive && !!onZoneClick;

        return (
          <g
            key={zone}
            onClick={() => isClickable && onZoneClick?.(zone)}
            style={{ cursor: isClickable ? "pointer" : "default" }}
          >
            <circle
              cx={x} cy={y} r={isFielder ? 11 : 9}
              fill={
                isLastShot ? "#ff6b35" :
                isFielder ? "#e8e020" :
                interactive ? "#4488cc" : "#1155aa"
              }
              stroke={isFielder ? "#fff" : "#aac"}
              strokeWidth={isFielder ? 2 : 1}
              opacity={isFielder ? 1 : 0.55}
            />
            <text
              x={x} y={y + 20}
              fontSize="8"
              fill={isFielder ? "#fff" : "#cde"}
              textAnchor="middle"
              fontFamily="sans-serif"
              fontWeight={isFielder ? "bold" : "normal"}
              opacity={isFielder ? 1 : 0.7}
            >
              {ZONE_LABELS[zone]}
            </text>
          </g>
        );
      })}

      {/* Batter marker */}
      <circle cx="300" cy="230" r="7" fill="#ff8844" stroke="#fff" strokeWidth="2" />
      <text x="300" y="248" fontSize="8" fill="#fff" textAnchor="middle" fontFamily="sans-serif">BAT</text>

      {/* Legend */}
      {interactive && (
        <g>
          <circle cx="20" cy="400" r="6" fill="#e8e020" />
          <text x="30" y="404" fontSize="9" fill="#cde" fontFamily="sans-serif">Fielder set</text>
          <circle cx="100" cy="400" r="6" fill="#4488cc" opacity="0.55" />
          <text x="112" y="404" fontSize="9" fill="#cde" fontFamily="sans-serif">Click to place</text>
        </g>
      )}
    </svg>
  );
}
