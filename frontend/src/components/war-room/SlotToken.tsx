"use client";

import { useEffect, useState, type ReactNode } from "react";
import { num, ratingColor } from "@/lib/format";
import type { AnyPlayer, Need } from "@/lib/types";

/** Fades content in from 4px below on mount. Used only for the player who was just placed. */
export function SettleIn({ active, children }: { active: boolean; children: ReactNode }) {
  const [shown, setShown] = useState(!active);
  useEffect(() => {
    if (!active) return;
    const raf = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(raf);
  }, [active]);
  return (
    <div
      className={`transition-[opacity,transform] duration-base ease-out ${
        shown ? "translate-y-0 opacity-100" : "translate-y-1 opacity-0"
      }`}
    >
      {children}
    </div>
  );
}

export function OvrRing({ ovr, size = "md" }: { ovr: number; size?: "sm" | "md" }) {
  return (
    <span
      aria-hidden
      className={`tabular inline-flex shrink-0 items-center justify-center rounded-full bg-bg font-display font-bold leading-none text-ink ${
        size === "sm" ? "h-6 w-6 border-2 text-[11px]" : "h-9 w-9 border-[3px] text-base"
      }`}
      style={{ borderColor: ratingColor(ovr) }}
    >
      {ovr}
    </span>
  );
}

const lastName = (n: string) => n.split(" ").slice(1).join(" ") || n;
const shortName = (n: string) => {
  const [first, ...rest] = n.split(" ");
  return rest.length && first ? `${first[0]}. ${rest.join(" ")}` : n;
};

interface Props {
  slot: string;
  player: AnyPlayer | null;
  need: Need | undefined;
  /** A player is selected and waiting to be put somewhere. */
  armedName: string | null;
  compact: boolean;
  settle: boolean;
  disabled: boolean;
  onActivate: () => void;
}

export function SlotToken({ slot, player, need, armedName, compact, settle, disabled, onActivate }: Props) {
  const armed = armedName !== null;
  const flag = need ? (need.severity === "empty" || !player ? "Empty" : "Weak") : null;
  const label = armed
    ? `Put ${armedName} at ${slot}${player ? `, replacing ${player.name}` : ""}`
    : player
      ? `${slot}: ${player.name}, OVR ${player.ovr}, ${num(player.war)} sWAR${flag ? `, ${flag.toLowerCase()} spot` : ""}. Open details`
      : `${slot}: empty. Find a player on the skill map`;

  const border = armed
    ? "border-accent"
    : !player
      ? "border-dashed border-ink-3"
      : flag
        ? "border-bad"
        : "border-line";

  return (
    <SettleIn key={player?.id ?? "empty"} active={settle}>
      <button
        type="button"
        onClick={onActivate}
        disabled={disabled}
        aria-label={label}
        title={need?.message ?? player?.name ?? `${slot} is empty`}
        className={`group flex flex-col rounded border-2 bg-surface text-left transition-colors duration-fast ease-out hover:bg-surface-2 disabled:cursor-wait ${border} ${
          compact ? "w-[4.75rem] gap-0.5 px-1.5 py-1" : "w-[8.5rem] gap-1 px-2 py-1.5"
        }`}
      >
        <span className="flex items-center justify-between gap-1 font-display text-[13px] font-bold leading-none tracking-wide">
          <span className={armed ? "text-accent-text" : flag ? "text-bad" : "text-ink-2"}>{slot}</span>
          {compact && player && <OvrRing ovr={player.ovr} size="sm" />}
          {!compact && flag && !armed && <span className="text-[11px] text-bad">{flag}</span>}
          {!compact && armed && <span className="text-[11px] text-accent-text">Put here</span>}
        </span>
        {player ? (
          compact ? (
            <span className="block truncate text-xs font-semibold leading-tight">{lastName(player.name)}</span>
          ) : (
            <span className="flex items-center gap-2">
              <OvrRing ovr={player.ovr} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-semibold leading-tight">{shortName(player.name)}</span>
                <span className="tabular block text-[11px] leading-tight text-ink-2">{num(player.war)} sWAR</span>
              </span>
            </span>
          )
        ) : (
          <span className={`text-ink-3 ${compact ? "text-[11px]" : "py-2 text-xs"}`}>No starter</span>
        )}
      </button>
    </SettleIn>
  );
}
