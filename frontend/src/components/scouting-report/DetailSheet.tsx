"use client";

import { useEffect, useRef, useState } from "react";
import { PlayerDetail } from "@/components/PlayerDetail";
import s from "./scouting.module.css";

interface Props {
  playerId: number | null;
  planSeason: number;
  statsSeason: number;
  archetypeLabels: Record<string, string>;
  onSelectPlayer: (id: number) => void;
  onClose: () => void;
}

/** Full scouting report in a right-hand side sheet. Escape closes; focus returns to the opener. */
export function DetailSheet({ playerId, planSeason, statsSeason, archetypeLabels, onSelectPlayer, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const [shown, setShown] = useState(false);
  const open = playerId !== null;

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      dialog.showModal();
      const raf = requestAnimationFrame(() => setShown(true));
      return () => cancelAnimationFrame(raf);
    }
    if (!open && dialog.open) {
      dialog.close();
    }
    return undefined;
  }, [open]);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    const handleClose = () => {
      setShown(false);
      onClose();
      const el = opener.current;
      opener.current = null;
      if (el?.isConnected) el.focus({ preventScroll: true });
    };
    dialog.addEventListener("close", handleClose);
    return () => dialog.removeEventListener("close", handleClose);
  }, [onClose]);

  return (
    <dialog
      ref={ref}
      aria-labelledby="sr-sheet-title"
      onClick={(e) => e.target === ref.current && ref.current?.close()}
      className="m-0 ml-auto h-full max-h-none w-full max-w-xl bg-transparent p-0 text-ink backdrop:bg-ink/40"
    >
      <div
        className={`${s.sheetPanel} ${shown ? "" : s.sheetHidden} flex h-full flex-col border-l border-line bg-surface`}
      >
        <header className="flex items-center gap-2 border-b border-line px-5 py-2">
          <h2 id="sr-sheet-title" className="flex-1 text-sm font-semibold text-ink-2">
            Full scouting report
          </h2>
          <button
            type="button"
            onClick={() => ref.current?.close()}
            className="min-h-10 rounded px-3 text-sm font-semibold text-ink-2 transition-colors duration-fast ease-out hover:bg-surface-2 hover:text-ink"
          >
            Close report
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-5">
          {playerId !== null && (
            <PlayerDetail
              key={playerId}
              playerId={playerId}
              planSeason={planSeason}
              statsSeason={statsSeason}
              archetypeLabels={archetypeLabels}
              onSelectPlayer={onSelectPlayer}
            />
          )}
        </div>
      </div>
    </dialog>
  );
}
