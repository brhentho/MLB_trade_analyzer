"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RATING_LABELS, ratingKeys, ratingWord } from "@/lib/format";
import type { AnyPlayer, Group, RatingKey, Ratings } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import { Fingerprint } from "@/components/viz/Fingerprint";
import { PlayerList } from "./PlayerList";

const flat = (group: Group): Record<string, number> => Object.fromEntries(ratingKeys(group).map((k) => [k, 50]));

interface Props {
  group: Group;
  onRoster: Set<number>;
  armedId: number | null;
  onPick: (p: AnyPlayer, el: HTMLElement | null) => void;
}

/** Draw the shape you want with one slider per rating; nearest real players update as you drag. */
export function ShapeDrawer({ group, onRoster, armedId, onPick }: Props) {
  const [profiles, setProfiles] = useState<Record<Group, Record<string, number>>>({
    hitter: { ...flat("hitter"), power: 65, eye: 60 },
    pitcher: { ...flat("pitcher"), stuff: 65, control: 60 },
  });
  const profile = profiles[group];
  const key = JSON.stringify(profile);
  const [debounced, setDebounced] = useState(key);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(key), 250);
    return () => clearTimeout(t);
  }, [key]);

  const result = useAsync(() => api.shape(group, JSON.parse(debounced) as Ratings, 12), [group, debounced]);
  const set = (k: RatingKey, v: number) => setProfiles((all) => ({ ...all, [group]: { ...all[group], [k]: v } }));

  return (
    <div className="space-y-4">
      <div className="grid items-center gap-4 sm:grid-cols-[minmax(0,1fr)_9rem]">
        <fieldset className="min-w-0 space-y-1">
          <legend className="mb-1 text-xs text-ink-3">Set each rating (20–80, 50 is average)</legend>
          {ratingKeys(group).map((k) => {
            const v = profile[k] ?? 50;
            return (
              <label key={k} className="grid grid-cols-[6.5rem_minmax(0,1fr)_2rem] items-center gap-2 text-sm">
                <span className="truncate text-ink-2">{RATING_LABELS[k]}</span>
                <input
                  type="range"
                  min={20}
                  max={80}
                  step={5}
                  value={v}
                  onChange={(e) => set(k, Number(e.target.value))}
                  aria-valuetext={`${v}, ${ratingWord(v)}`}
                  className="h-10 w-full accent-[rgb(var(--accent))]"
                />
                <span className="tabular text-right font-semibold">{v}</span>
              </label>
            );
          })}
        </fieldset>
        <div className="flex flex-col items-center gap-2">
          <Fingerprint group={group} ratings={profile} size={136} labels title="The shape you drew" />
          <button
            type="button"
            onClick={() => setProfiles((all) => ({ ...all, [group]: flat(group) }))}
            className="min-h-9 rounded px-2 text-xs font-semibold text-ink-2 hover:bg-surface-2"
          >
            Reset to average
          </button>
        </div>
      </div>

      <section aria-label="Closest players">
        <h3 className="mb-1 font-display text-lg font-bold">Closest real players</h3>
        {result.status === "error" ? (
          <ErrorState message={result.error} onRetry={result.reload} />
        ) : !result.data ? (
          <LoadingRows label="Finding players with this shape…" rows={5} />
        ) : result.data.results.length === 0 ? (
          <EmptyState title="No players match this shape">Pull a slider back toward 50.</EmptyState>
        ) : (
          <div className={`transition-opacity duration-fast ease-out ${result.status === "loading" ? "opacity-60" : ""}`}>
            <PlayerList
              players={result.data.results.map((r) => r.player)}
              extra={(p) => {
                const r = result.data?.results.find((x) => x.player.id === p.id);
                return r ? `${Math.round(r.similarity)}% match` : null;
              }}
              sortable={false}
              onRoster={onRoster}
              armedId={armedId}
              onPick={onPick}
            />
          </div>
        )}
      </section>
    </div>
  );
}
