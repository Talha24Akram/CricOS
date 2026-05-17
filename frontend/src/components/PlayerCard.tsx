"use client";

import React, { useState } from "react";

interface PlayerCardProps {
  id: number;
  name: string;
  role?: string;
  overall?: number;
  photo_url?: string;
  isSelected?: boolean;
  isCaptain?: boolean;
  isWK?: boolean;
  onClick?: () => void;
  onCaptain?: () => void;
  onWK?: () => void;
  compact?: boolean;
  disabled?: boolean;
}

const ROLE_COLORS: Record<string, string> = {
  batter: "text-emerald-400",
  bowler: "text-blue-400",
  all_rounder: "text-yellow-400",
  wicket_keeper: "text-purple-400",
};

const ROLE_LABELS: Record<string, string> = {
  batter: "BAT",
  bowler: "BOWL",
  all_rounder: "AR",
  wicket_keeper: "WK",
};

export default function PlayerCard({
  id,
  name,
  role = "all_rounder",
  overall = 50,
  photo_url,
  isSelected = false,
  isCaptain = false,
  isWK = false,
  onClick,
  onCaptain,
  onWK,
  compact = false,
  disabled = false,
}: PlayerCardProps) {
  const [imgErr, setImgErr] = useState(false);

  const roleColor = ROLE_COLORS[role] || "text-zinc-400";
  const roleLabel = ROLE_LABELS[role] || role.toUpperCase();

  const overallColor =
    overall >= 85 ? "text-yellow-400" :
    overall >= 70 ? "text-emerald-400" :
    overall >= 55 ? "text-blue-400" : "text-zinc-400";

  if (compact) {
    return (
      <div
        onClick={onClick}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all
          ${isSelected ? "bg-emerald-800 ring-1 ring-emerald-500" : "bg-zinc-800 hover:bg-zinc-700"}
        `}
      >
        <div className="w-8 h-8 rounded-full overflow-hidden bg-zinc-700 flex-shrink-0">
          {photo_url && !imgErr ? (
            <img src={photo_url} alt={name} className="w-full h-full object-cover" onError={() => setImgErr(true)} />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-zinc-500 text-xs">👤</div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white truncate">{name}</div>
          <div className="flex items-center gap-1">
            <span className={`text-xs font-bold ${roleColor}`}>{roleLabel}</span>
            {isCaptain && <span className="text-xs bg-yellow-600 text-black px-1 rounded font-bold">C</span>}
            {isWK && <span className="text-xs bg-purple-600 text-white px-1 rounded font-bold">WK</span>}
          </div>
        </div>
        <span className={`text-sm font-bold ${overallColor}`}>{overall}</span>
      </div>
    );
  }

  return (
    <div
      onClick={disabled && !isSelected ? undefined : onClick}
      className={`
        flex flex-col items-center p-3 rounded-xl transition-all relative
        ${disabled && !isSelected ? "opacity-35 cursor-not-allowed" : "cursor-pointer"}
        ${isSelected
          ? "ring-2 ring-emerald-500"
          : disabled
          ? "bg-zinc-900"
          : "bg-zinc-800 hover:bg-zinc-700"}
      `}
      style={isSelected ? { background: "rgba(0,209,178,0.12)", border: "2px solid rgba(0,209,178,0.5)" } : {}}
    >
      {/* Badges */}
      <div className="absolute top-1 left-1 flex gap-1">
        {isCaptain && <span className="text-xs bg-yellow-500 text-black px-1.5 py-0.5 rounded font-bold">C</span>}
        {isWK && <span className="text-xs bg-purple-600 text-white px-1.5 py-0.5 rounded font-bold">WK</span>}
      </div>

      {/* Photo */}
      <div className="w-16 h-16 rounded-full overflow-hidden bg-zinc-700 mb-2">
        {photo_url && !imgErr ? (
          <img src={photo_url} alt={name} className="w-full h-full object-cover" onError={() => setImgErr(true)} />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-2xl">👤</div>
        )}
      </div>

      <div className="text-xs font-bold text-center text-white leading-tight mb-1">{name}</div>
      <div className="flex items-center gap-2">
        <span className={`text-xs font-bold ${roleColor}`}>{roleLabel}</span>
        <span className={`text-sm font-bold ${overallColor}`}>{overall}</span>
      </div>

      {/* Captain / WK buttons */}
      {(onCaptain || onWK) && (
        <div className="flex gap-1 mt-2">
          {onCaptain && (
            <button
              onClick={(e) => { e.stopPropagation(); onCaptain(); }}
              className={`text-xs px-2 py-1 rounded transition-all
                ${isCaptain ? "bg-yellow-500 text-black font-bold" : "bg-zinc-600 text-zinc-300 hover:bg-zinc-500"}`}
            >
              C
            </button>
          )}
          {onWK && (
            <button
              onClick={(e) => { e.stopPropagation(); onWK(); }}
              className={`text-xs px-2 py-1 rounded transition-all
                ${isWK ? "bg-purple-600 text-white font-bold" : "bg-zinc-600 text-zinc-300 hover:bg-zinc-500"}`}
            >
              WK
            </button>
          )}
        </div>
      )}
    </div>
  );
}
