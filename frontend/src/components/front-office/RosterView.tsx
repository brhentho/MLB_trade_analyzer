"use client";

import { ErrorState, LoadingRows } from "@/components/States";
import { PayrollLedger } from "@/components/viz/PayrollLedger";
import { api } from "@/lib/api";
import { money, num } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { Meta } from "@/lib/types";
import { PlayerTable } from "./PlayerTable";

interface Props {
  team: string;
  meta: Meta;
  selectedId: number | null;
  onSelect: (id: number) => void;
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "good" | "bad" | undefined }) {
  return (
    <div>
      <dt className="text-xs text-ink-3">{label}</dt>
      <dd className={`tabular text-lg font-semibold ${tone === "bad" ? "text-bad" : tone === "good" ? "text-good" : ""}`}>
        {value}
      </dd>
    </div>
  );
}

/** S1: take over a team. */
export function RosterView({ team, meta, selectedId, onSelect }: Props) {
  const roster = useAsync(() => api.roster(team), [team]);
  if (roster.status === "error") return <ErrorState message={roster.error} onRetry={roster.reload} />;
  if (!roster.data) return <LoadingRows label="Loading roster…" rows={10} />;
  const { players, evaluation: ev, team: t } = roster.data;
  const plan = meta.plan_season;
  const hitters = players.filter((p) => p.group === "hitter");
  const pitchers = players.filter((p) => p.group === "pitcher");

  return (
    <div className={`space-y-6 transition-opacity duration-fast ease-out ${roster.status === "loading" ? "opacity-60" : ""}`}>
      <section aria-labelledby="ledger-h" className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div>
          <h2 id="ledger-h" className="mb-3 text-sm font-semibold">
            {t.name} committed payroll
          </h2>
          <PayrollLedger
            players={players}
            planSeason={plan}
            cbt={ev.cbt_threshold}
            highlightIds={selectedId ? [selectedId] : []}
            onSelect={onSelect}
          />
        </div>
        <div className="space-y-4">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Stat label={`${plan} payroll`} value={money(ev.payroll_now, 1)} />
            <Stat
              label="Room under tax"
              value={money(ev.cbt_room, 1)}
              tone={ev.cbt_room < 0 ? "bad" : undefined}
            />
            <Stat label={`sWAR ${meta.stats_season}`} value={num(ev.war)} />
            <Stat label={`Projected ${plan}`} value={num(ev.proj_war)} />
          </dl>
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-ink-3">
              Holes to fill <span className="tabular">({ev.needs.length})</span>
            </h3>
            {ev.needs.length === 0 ? (
              <p className="text-sm text-ink-2">Every lineup slot and pitching role is covered.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {ev.needs.map((n) => (
                  <li key={`${n.slot}-${n.message}`} className="flex gap-2">
                    <span
                      className={`tabular mt-0.5 inline-flex h-5 min-w-[2rem] justify-center rounded-sm px-1 text-xs font-semibold ${
                        n.severity === "empty" ? "bg-bad/20 text-bad" : "bg-surface-2 text-ink-2"
                      }`}
                    >
                      {n.slot}
                    </span>
                    <span className="text-ink-2">{n.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <p className="text-xs text-ink-3">
            <span className="tabular">{ev.expiring.length}</span> players reach free agency after {plan}. * marks an
            estimated salary.
          </p>
        </div>
      </section>

      <section aria-labelledby="hitters-h">
        <h2 id="hitters-h" className="mb-2 text-sm font-semibold">
          Position players <span className="tabular text-ink-3">{hitters.length}</span>
        </h2>
        <PlayerTable group="hitter" players={hitters} planSeason={plan} caption={`${t.name} position players`} selectedId={selectedId} onSelect={onSelect} />
      </section>
      <section aria-labelledby="pitchers-h">
        <h2 id="pitchers-h" className="mb-2 text-sm font-semibold">
          Pitchers <span className="tabular text-ink-3">{pitchers.length}</span>
        </h2>
        <PlayerTable group="pitcher" players={pitchers} planSeason={plan} caption={`${t.name} pitchers`} selectedId={selectedId} onSelect={onSelect} />
      </section>
    </div>
  );
}
