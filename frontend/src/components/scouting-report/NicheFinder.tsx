"use client";

import { FilterChips, ScoutQueryBox, useScoutSearch } from "@/components/ScoutSearch";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import type { Archetype, Group } from "@/lib/types";
import type { LabData } from "@/lib/useLabData";
import { PlayerCard } from "./PlayerCard";

const EXAMPLES = [
  "Lefty reliever, elite chase rate, under $6M, 2+ years of control",
  "Cheap shortstop with a plus glove",
  "Young power bat under 26",
];

interface Props {
  lab: LabData;
  onOpen: (id: number) => void;
}

function ArchetypeShelf({
  title,
  items,
  active,
  busy,
  onPick,
}: {
  title: string;
  items: Archetype[];
  active: string | undefined;
  busy: boolean;
  onPick: (id: string) => void;
}) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold text-ink-3">{title}</h4>
      <ul className="-mx-4 flex scroll-px-4 gap-2 overflow-x-auto px-4 pb-1 lg:mx-0 lg:flex-wrap lg:overflow-visible lg:px-0 lg:pb-0">
        {items.map((a) => (
          <li key={a.id} className="shrink-0">
            <button
              type="button"
              disabled={busy}
              aria-pressed={active === a.id}
              onClick={() => onPick(a.id)}
              title={a.description}
              className={`inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded border px-3 text-sm transition-colors duration-fast ease-out disabled:opacity-60 ${
                active === a.id ? "border-ink bg-ink text-surface" : "border-line bg-surface text-ink hover:border-ink-3"
              }`}
            >
              <span className="font-semibold">{a.label}</span>
              <span className={`tabular text-xs ${active === a.id ? "text-surface" : "text-ink-3"}`}>{a.count}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function NicheFinder({ lab, onOpen }: Props) {
  const { state, runQuery, runFilters, dropChip } = useScoutSearch(24);
  const busy = state.status === "loading";
  const activeArchetype = state.filters?.archetypes?.length === 1 ? state.filters.archetypes[0] : undefined;
  const byGroup = (g: Group) => lab.archetypes.filter((a) => a.group === g);
  const results = state.result?.results ?? [];

  const retry = () => {
    if (state.filters) void runFilters(state.filters);
    else void runQuery(state.query);
  };

  return (
    <div className="grid gap-x-8 gap-y-6 lg:grid-cols-[16rem_1fr]">
      <div className="min-w-0 lg:col-start-2 lg:row-start-1">
        <ScoutQueryBox onSubmit={(q) => void runQuery(q)} busy={busy} examples={EXAMPLES} />
      </div>

      <section
        aria-labelledby="sr-archetypes"
        className="min-w-0 space-y-4 lg:sticky lg:top-6 lg:col-start-1 lg:row-span-2 lg:row-start-1 lg:self-start"
      >
        <h3 id="sr-archetypes" className="text-sm font-semibold text-ink-2">
          Browse by archetype
        </h3>
        <ArchetypeShelf
          title="Hitters"
          items={byGroup("hitter")}
          active={activeArchetype}
          busy={busy}
          onPick={(id) => void runFilters({ archetypes: [id], sort: "ovr", descending: true })}
        />
        <ArchetypeShelf
          title="Pitchers"
          items={byGroup("pitcher")}
          active={activeArchetype}
          busy={busy}
          onPick={(id) => void runFilters({ archetypes: [id], sort: "ovr", descending: true })}
        />
      </section>

      <div className="min-w-0 lg:col-start-2 lg:row-start-2">
        <div className="min-h-7">
          {state.filters && (
            <FilterChips
              filters={state.filters}
              archetypeLabels={lab.archetypeLabels}
              onRemove={(id) => void dropChip(id)}
              interpretedBy={state.interpretedBy}
              notes={state.notes}
            />
          )}
        </div>

        <div className="mt-4" aria-live="polite" aria-busy={busy}>
          {state.status === "error" && <ErrorState message={state.error ?? "The search failed."} onRetry={retry} />}
          {busy && results.length === 0 && <LoadingRows label="Searching the league…" rows={5} />}
          {state.status === "idle" && (
            <EmptyState title="Describe a player or pick an archetype">
              Each card shows the reasons it matched, like a chase rate percentile or the salary in {lab.meta.plan_season}.
            </EmptyState>
          )}
          {state.status === "ready" && results.length === 0 && (
            <EmptyState title="No players match every constraint">Remove a chip above to widen the search.</EmptyState>
          )}
          {results.length > 0 && state.result && (
            <>
              <p className="tabular mb-3 text-sm text-ink-2">
                {busy ? "Updating results…" : `Showing ${results.length} of ${state.result.total} ${state.result.total === 1 ? "player" : "players"}`}
              </p>
              <ul
                className={`grid grid-cols-[repeat(auto-fill,12.5rem)] justify-center gap-x-4 gap-y-6 transition-opacity duration-base ease-out sm:justify-start ${busy ? "opacity-60" : ""}`}
              >
                {results.map(({ player, reasons }, i) => {
                  return (
                    <li key={player.id}>
                      <PlayerCard
                        player={player}
                        planSeason={lab.meta.plan_season}
                        statsSeason={lab.meta.stats_season}
                        onOpen={onOpen}
                        dealIndex={i}
                      >
                        <div aria-label={`Why ${player.name} matched`} role="group">
                          <p className="text-[11px] font-semibold text-ink-3">Matched on</p>
                          <ul className="mt-1 flex flex-wrap gap-1">
                            {reasons.map((r) => (
                              <li
                                key={r.label}
                                title={r.label}
                                className="tabular max-w-full truncate rounded-sm bg-surface-2 px-1.5 py-0.5 text-xs font-medium text-ink"
                              >
                                {r.label}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </PlayerCard>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
