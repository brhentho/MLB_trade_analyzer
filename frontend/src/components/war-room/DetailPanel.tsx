"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { PlayerDetail } from "@/components/PlayerDetail";
import type { Player } from "@/lib/types";

interface Props {
  playerId: number;
  planSeason: number;
  statsSeason: number;
  archetypeLabels: Record<string, string>;
  onClose: () => void;
  onSelectPlayer: (id: number) => void;
  actions: (p: Player) => ReactNode;
  status?: ReactNode;
}

/**
 * Non-modal side panel: the diamond stays clickable so a selected player can be put on it directly.
 * The caller handles Escape and returns focus to whatever opened it.
 */
export function DetailPanel({ playerId, planSeason, statsSeason, archetypeLabels, onClose, onSelectPlayer, actions, status }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus({ preventScroll: true });
  }, [playerId]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <aside
      aria-label="Player details"
      className="fixed inset-y-0 right-0 z-30 flex w-full max-w-[28rem] flex-col border-l border-line bg-surface"
    >
      <div className="flex items-center justify-between gap-2 border-b border-line px-4 py-2">
        <span className="text-xs text-ink-3">Player details</span>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          className="min-h-10 rounded px-3 text-sm font-semibold text-ink-2 hover:bg-surface-2"
        >
          Close <span className="text-ink-3">Esc</span>
        </button>
      </div>
      {status}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <PlayerDetail
          key={playerId}
          playerId={playerId}
          planSeason={planSeason}
          statsSeason={statsSeason}
          archetypeLabels={archetypeLabels}
          onSelectPlayer={onSelectPlayer}
          actions={actions}
        />
      </div>
    </aside>
  );
}
