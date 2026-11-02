"use client";

import { FilterChips, ScoutQueryBox, useScoutSearch } from "@/components/ScoutSearch";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import { BargainField } from "@/components/viz/BargainField";
import type { Archetype, Meta, Player, Reason } from "@/lib/types";
import { PlayerTable } from "./PlayerTable";

interface Props {
  meta: Meta;
  archetypes: Archetype[];
  archetypeLabels: Record<string, string>;
  selectedId: number | null;
  onSelect: (id: number) => void;
}

const EXAMPLES = [
  "Lefty reliever with elite chase rate under $6M",
  "Young shortstop with power and speed",
  "Cheap starter with plus control, 3+ years of control",
  "Patient eye outfielder",
];

/** S2/S3: describe a niche, see it read back as chips, scan results in a grid and on the bargain field. */
export function ScoutView({ meta, archetypes, archetypeLabels, selectedId, onSelect }: Props) {
  const { state, runQuery, runFilters, dropChip } = useScoutSearch(60);
  const results = state.result?.results ?? [];
  const players: Player[] = results.map((r) => r.player);
  const reasons: Record<number, Reason[]> = Object.fromEntries(results.map((r) => [r.player.id, r.reasons]));
  const groups = { hitter: players.filter((p) => p.group === "hitter"), pitcher: players.filter((p) => p.group === "pitcher") };

  return (
    <div className="space-y-5">
      <ScoutQueryBox onSubmit={runQuery} busy={state.status === "loading"} examples={EXAMPLES} />

      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="text-ink-3">Or browse an archetype</span>
        {archetypes.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => runFilters({ group: a.group, archetypes: [a.id], sort: "war" })}
            title={a.description}
            className={`min-h-7 rounded border px-2 ${
              state.filters?.archetypes?.includes(a.id) ? "border-accent text-ink" : "border-line text-ink-2 hover:text-ink"
            }`}
          >
            {a.label} <span className="tabular text-ink-3">{a.count}</span>
          </button>
        ))}
      </div>

      {state.filters && (
        <FilterChips
          filters={state.filters}
          archetypeLabels={archetypeLabels}
          onRemove={dropChip}
          interpretedBy={state.interpretedBy}
          notes={state.notes}
        />
      )}

      {state.status === "error" && <ErrorState message={state.error ?? ""} />}
      {state.status === "loading" && !state.result && <LoadingRows label="Searching…" />}
      {state.status === "idle" && (
        <EmptyState title="Describe the player you need">
          Plain language works: position, handedness, skills, budget, years of control. Each part becomes a chip you can
          remove.
        </EmptyState>
      )}
      {state.result && state.result.total === 0 && (
        <EmptyState title="No players match every constraint">Remove a chip to widen the search.</EmptyState>
      )}

      {state.result && state.result.total > 0 && (
        <div className={`space-y-6 transition-opacity duration-fast ease-out ${state.status === "loading" ? "opacity-60" : ""}`}>
          <p className="text-sm text-ink-2" aria-live="polite">
            <span className="tabular font-semibold text-ink">{state.result.total}</span>{" "}
            {state.result.total === 1 ? "player matches" : "players match"}
            {state.result.total > players.length && <>; showing the top {players.length} by sWAR</>}.
          </p>
          <section aria-labelledby="bargain-h" className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
            <div>
              <h2 id="bargain-h" className="mb-1 text-sm font-semibold">
                Value against cost
              </h2>
              <BargainField
                players={players}
                dollarsPerWar={meta.assumptions.dollars_per_war_m}
                selectedId={selectedId}
                onSelect={onSelect}
              />
            </div>
            <p className="self-end text-xs text-ink-3">
              Each dot is a match. Above the dashed market-rate line, a player projects to be worth more than he&apos;s
              paid at {`$${meta.assumptions.dollars_per_war_m}M`} per win. Upper left is where bargains live.
            </p>
          </section>
          {(["hitter", "pitcher"] as const).map(
            (g) =>
              groups[g].length > 0 && (
                <section key={g} aria-label={g === "hitter" ? "Matching position players" : "Matching pitchers"}>
                  <h2 className="mb-2 text-sm font-semibold">{g === "hitter" ? "Position players" : "Pitchers"}</h2>
                  <PlayerTable
                    group={g}
                    players={groups[g]}
                    planSeason={meta.plan_season}
                    caption="Search results"
                    reasons={reasons}
                    selectedId={selectedId}
                    onSelect={onSelect}
                    showTeam
                  />
                </section>
              ),
          )}
        </div>
      )}
    </div>
  );
}
