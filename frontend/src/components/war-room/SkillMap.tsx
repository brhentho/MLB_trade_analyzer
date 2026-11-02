"use client";

import { useMemo } from "react";
import type { AnyPlayer, Archetype, Group, PlayerSummary } from "@/lib/types";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import { Constellation } from "@/components/viz/Constellation";
import { PlayerList } from "./PlayerList";

export type Source =
  | { kind: "lasso"; ids: number[] }
  | { kind: "archetype"; id: string }
  | { kind: "search"; label: string; status: "loading" | "ready" | "error"; players: AnyPlayer[]; error?: string; retry?: () => void }
  | null;

interface Props {
  group: Group;
  players: { status: "loading" | "ready" | "error"; data: PlayerSummary[] | null; error: string | null; reload: () => void };
  archetypes: Archetype[];
  source: Source;
  onSource: (s: Source) => void;
  onRoster: Set<number>;
  armedId: number | null;
  onPick: (p: AnyPlayer, el: HTMLElement | null) => void;
}

/** Archetype constellation plus the list it produces. Archetype buttons are the keyboard way to lasso. */
export function SkillMap({ group, players, archetypes, source, onSource, onRoster, armedId, onPick }: Props) {
  const all = useMemo(() => players.data ?? [], [players.data]);
  const groupArchetypes = useMemo(
    () =>
      archetypes
        .filter((a) => a.group === group)
        .map((a) => ({ ...a, n: all.filter((p) => p.archetypes.includes(a.id)).length }))
        .filter((a) => a.n > 0),
    [archetypes, all, group],
  );

  const listed: AnyPlayer[] = useMemo(() => {
    if (!source) return [];
    if (source.kind === "lasso") {
      const s = new Set(source.ids);
      return all.filter((p) => s.has(p.id));
    }
    if (source.kind === "archetype") return all.filter((p) => p.archetypes.includes(source.id));
    return source.players;
  }, [all, source]);

  const selectedIds = listed.map((p) => p.id);
  const title =
    source?.kind === "lasso"
      ? `${listed.length} players in your lasso`
      : source?.kind === "archetype"
        ? (archetypes.find((a) => a.id === source.id)?.label ?? source.id)
        : source?.kind === "search"
          ? source.label
          : null;

  if (players.status === "error" && !players.data) return <ErrorState message={players.error ?? ""} onRetry={players.reload} />;

  return (
    <div className="space-y-3">
      {!players.data ? (
        <LoadingRows label="Loading the skill map…" rows={8} />
      ) : (
        <div className="rounded border border-line bg-bg">
          <Constellation
            players={all}
            archetypes={archetypes.filter((a) => a.group === group)}
            selectedIds={selectedIds}
            focusId={armedId}
            onBrush={(ids) => onSource({ kind: "lasso", ids })}
            onFocus={(id) => {
              const p = all.find((x) => x.id === id);
              if (p) onPick(p, null);
            }}
          />
        </div>
      )}
      <p className="text-xs text-ink-3">
        Nearby dots play alike. Drag across the map to lasso a region, or pick an archetype.
      </p>
      <div role="group" aria-label="Select an archetype" className="flex flex-wrap gap-1.5">
        {groupArchetypes.map((a) => {
          const on = source?.kind === "archetype" && source.id === a.id;
          return (
            <button
              key={a.id}
              type="button"
              aria-pressed={on}
              title={a.description}
              onClick={() => onSource(on ? null : { kind: "archetype", id: a.id })}
              className={`min-h-9 rounded-full border px-3 text-xs font-semibold transition-colors duration-fast ease-out ${
                on ? "border-ink bg-ink text-bg" : "border-line text-ink-2 hover:border-ink-3 hover:text-ink"
              }`}
            >
              {a.label} <span className="tabular font-normal opacity-80">{a.n}</span>
            </button>
          );
        })}
      </div>

      <section aria-label="Selected players">
        <p className="sr-only" role="status">
          {title ? `${title}: ${listed.length} players listed` : ""}
        </p>
        {title && (
          <div className="mb-1 flex items-center justify-between gap-2">
            <h3 className="truncate font-display text-lg font-bold">{title}</h3>
            <button
              type="button"
              onClick={() => onSource(null)}
              className="min-h-9 shrink-0 rounded px-2 text-xs font-semibold text-ink-2 hover:bg-surface-2"
            >
              Clear selection
            </button>
          </div>
        )}
        {source?.kind === "search" && source.status === "loading" ? (
          <LoadingRows label="Finding players…" rows={5} />
        ) : source?.kind === "search" && source.status === "error" ? (
          <ErrorState message={source.error ?? ""} {...(source.retry ? { onRetry: source.retry } : {})} />
        ) : !source ? (
          <EmptyState title="No players selected yet">
            Drag across the map, pick an archetype, or choose “Find a replacement” under a weak spot.
          </EmptyState>
        ) : listed.length === 0 ? (
          <EmptyState title="Nobody in that region">Try a wider lasso or another archetype.</EmptyState>
        ) : (
          <PlayerList players={listed} onRoster={onRoster} armedId={armedId} onPick={onPick} />
        )}
      </section>
    </div>
  );
}
