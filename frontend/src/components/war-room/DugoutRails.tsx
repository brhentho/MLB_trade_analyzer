"use client";

import { useState } from "react";
import { num, positionLabel } from "@/lib/format";
import type { AnyPlayer, Need, Player } from "@/lib/types";
import { OvrRing, SettleIn } from "./SlotToken";

interface RailProps {
  title: string;
  ids: number[];
  players: Record<number, Player>;
  limit?: number;
  slots?: number;
  need?: Need | undefined;
  armedName: string | null;
  putLabel: string;
  settleId: number | null;
  disabled: boolean;
  onPut?: () => void;
  onOpen: (id: number, el: HTMLElement) => void;
}

function Rail({ title, ids, players, limit, slots, need, armedName, putLabel, settleId, disabled, onPut, onOpen }: RailProps) {
  const [all, setAll] = useState(false);
  const shown = limit && !all ? ids.slice(0, limit) : ids;
  const empties = slots ? Math.max(0, slots - ids.length) : 0;
  return (
    <section aria-label={title} className="min-w-0">
      <header className="flex items-baseline justify-between gap-2 border-b border-line pb-1">
        <h3 className="font-display text-base font-bold tracking-wide">
          {title} <span className="tabular text-sm font-semibold text-ink-3">{ids.length}</span>
        </h3>
        {need && !armedName && (
          <span className="text-xs font-semibold text-bad" title={need.message}>
            {need.severity === "empty" ? "Short" : "Weak"}
          </span>
        )}
      </header>
      {armedName && onPut && (
        <button
          type="button"
          onClick={onPut}
          disabled={disabled}
          className="mt-1.5 flex min-h-10 w-full items-center rounded border-2 border-accent bg-surface px-2 text-left text-sm font-semibold hover:bg-surface-2 disabled:cursor-wait"
        >
          <span className="truncate">
            {putLabel} {armedName}
          </span>
        </button>
      )}
      {need && <p className="sr-only">{need.message}</p>}
      <ol className="mt-1">
        {shown.map((id) => {
          const p = players[id];
          if (!p) return null;
          return (
            <li key={id}>
              <SettleIn active={id === settleId}>
                <button
                  type="button"
                  onClick={(e) => onOpen(id, e.currentTarget)}
                  className="flex min-h-10 w-full items-center gap-2 rounded-sm px-1 text-left text-sm hover:bg-surface-2"
                  aria-label={`${p.name}, ${positionLabel(p)}, OVR ${p.ovr}, ${num(p.war)} sWAR. Open details`}
                >
                  <OvrRing ovr={p.ovr} size="sm" />
                  <span className="min-w-0 flex-1 truncate">{p.name}</span>
                  <span className="tabular w-9 text-right text-xs text-ink-2">{num(p.war)}</span>
                </button>
              </SettleIn>
            </li>
          );
        })}
        {Array.from({ length: empties }, (_, i) => (
          <li key={`empty-${i}`} className="flex min-h-10 items-center px-1 text-sm text-ink-3">
            Open spot
          </li>
        ))}
      </ol>
      {limit && ids.length > limit && (
        <button
          type="button"
          onClick={() => setAll((v) => !v)}
          className="mt-1 min-h-10 px-1 text-xs font-semibold text-ink-2 underline-offset-2 hover:underline"
        >
          {all ? `Show top ${limit}` : `Show all ${ids.length}`}
        </button>
      )}
    </section>
  );
}

interface Props {
  rotation: number[];
  bullpen: number[];
  bench: number[];
  players: Record<number, Player>;
  needs: Need[];
  armed: AnyPlayer | null;
  settleId: number | null;
  disabled: boolean;
  onPut: (target: "rotation" | "bullpen") => void;
  onOpen: (id: number, el: HTMLElement) => void;
}

/** Rotation, bullpen and bench, read like the rails of a dugout beside the field. */
export function DugoutRails({ rotation, bullpen, bench, players, needs, armed, settleId, disabled, onPut, onOpen }: Props) {
  const armedPitcher = armed && armed.group === "pitcher" ? armed.name : null;
  const spNeed = needs.find((n) => n.slot === "SP");
  const rpNeed = needs.find((n) => n.slot === "RP");
  return (
    <div className="grid gap-5 sm:grid-cols-3 xl:grid-cols-1">
      <Rail
        title="Rotation"
        ids={rotation}
        players={players}
        slots={5}
        need={spNeed}
        armedName={armedPitcher}
        putLabel="Put in rotation:"
        settleId={settleId}
        disabled={disabled}
        onPut={() => onPut("rotation")}
        onOpen={onOpen}
      />
      <Rail
        title="Bullpen"
        ids={bullpen}
        players={players}
        limit={8}
        need={rpNeed}
        armedName={armedPitcher}
        putLabel="Put in bullpen:"
        settleId={settleId}
        disabled={disabled}
        onPut={() => onPut("bullpen")}
        onOpen={onOpen}
      />
      <Rail
        title="Bench"
        ids={bench}
        players={players}
        limit={5}
        armedName={null}
        putLabel=""
        settleId={settleId}
        disabled={disabled}
        onOpen={onOpen}
      />
    </div>
  );
}
