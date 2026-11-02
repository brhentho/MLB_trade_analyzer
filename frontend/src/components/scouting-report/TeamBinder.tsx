"use client";

import { useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { PayrollLedger } from "@/components/viz/PayrollLedger";
import { api } from "@/lib/api";
import { LINEUP_ORDER, money, num } from "@/lib/format";
import type { Need, Player } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import type { LabData } from "@/lib/useLabData";
import { EmptySleeve, PlayerCard } from "./PlayerCard";

const COLLAPSED = 8;

interface Props {
  lab: LabData;
  onOpen: (id: number) => void;
}

function Sleeves({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <ul
      aria-label={label}
      className="-mx-4 flex snap-x scroll-px-4 gap-4 overflow-x-auto px-4 pb-3 sm:mx-0 sm:grid sm:grid-cols-[repeat(auto-fill,12.5rem)] sm:overflow-visible sm:px-0 sm:pb-0"
    >
      {children}
    </ul>
  );
}

function BinderPage({
  title,
  count,
  players,
  lab,
  onOpen,
  roleLabel,
}: {
  title: string;
  count: number;
  players: Player[];
  lab: LabData;
  onOpen: (id: number) => void;
  roleLabel?: (i: number) => string;
}) {
  const [all, setAll] = useState(false);
  const shown = all ? players : players.slice(0, COLLAPSED);
  const id = `binder-${title.toLowerCase()}`;
  return (
    <section aria-labelledby={id} className="mt-10">
      <h3 id={id} className="mb-3 flex items-baseline gap-2">
        <span className="font-display text-2xl font-bold">{title}</span>
        <span className="tabular text-sm text-ink-3">{count}</span>
      </h3>
      {players.length === 0 ? (
        <EmptyState title={`No ${title.toLowerCase()} on the roster`} />
      ) : (
        <Sleeves label={title}>
          {shown.map((p, i) => (
            <li key={p.id} className="flex flex-col gap-1.5">
              {roleLabel && <span className="tabular text-xs font-semibold text-ink-2">{roleLabel(i)}</span>}
              <PlayerCard
                player={p}
                planSeason={lab.meta.plan_season}
                statsSeason={lab.meta.stats_season}
                onOpen={onOpen}
              />
            </li>
          ))}
        </Sleeves>
      )}
      {players.length > COLLAPSED && (
        <button
          type="button"
          onClick={() => setAll((v) => !v)}
          aria-expanded={all}
          className="mt-3 min-h-10 rounded border border-line px-3 text-sm font-semibold text-ink transition-colors duration-fast ease-out hover:border-ink-3"
        >
          {all ? `Show first ${COLLAPSED}` : `Show all ${players.length}`}
        </button>
      )}
    </section>
  );
}

const SEVERITY_WORD: Record<Need["severity"], string> = { empty: "Empty", weak: "Weak" };

export function TeamBinder({ lab, onOpen }: Props) {
  const [team, setTeam] = useState("SEA");
  const roster = useAsync(() => api.roster(team), [team]);
  const plan = lab.meta.plan_season;

  const view = useMemo(() => {
    const r = roster.data;
    if (!r) return null;
    const byId = new Map(r.players.map((p) => [p.id, p]));
    const pick = (ids: number[]) => ids.map((i) => byId.get(i)).filter((p): p is Player => !!p);
    const ev = r.evaluation;
    const payroll = ev.payroll[String(plan)] ?? ev.payroll_now;
    return {
      r,
      ev,
      payroll,
      room: ev.cbt_threshold - payroll,
      lineup: LINEUP_ORDER.map((slot) => {
        const pid = ev.depth.lineup[slot];
        return { slot, player: pid == null ? undefined : byId.get(pid) };
      }),
      rotation: pick(ev.depth.rotation),
      bullpen: pick(ev.depth.bullpen),
      bench: pick(ev.depth.bench),
      weak: new Map(ev.needs.map((n) => [n.slot, n.severity])),
    };
  }, [roster.data, plan]);

  const teamName = lab.teams.find((t) => t.abbrev === team)?.name ?? team;
  const stale = roster.status === "loading" && view !== null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <TeamPicker teams={lab.teams} value={team} onChange={setTeam} label="Take over" id="sr-binder-team" />
        <span role="status" aria-live="polite" className="text-sm text-ink-2">
          {stale ? `Opening the ${teamName} binder…` : ""}
        </span>
      </div>

      {roster.status === "error" && (
        <div className="mt-6">
          <ErrorState message={roster.error} onRetry={roster.reload} />
        </div>
      )}
      {!view && roster.status === "loading" && (
        <div className="mt-6">
          <LoadingRows label={`Opening the ${teamName} binder…`} rows={6} />
        </div>
      )}

      {view && (
        <div
          aria-busy={stale}
          className={`mt-6 grid gap-x-8 gap-y-8 transition-opacity duration-base ease-out lg:grid-cols-[16rem_1fr] ${stale ? "opacity-60" : ""}`}
        >
          <aside className="space-y-8 lg:sticky lg:top-6 lg:self-start" aria-label={`${view.r.team.name} summary`}>
            <section aria-labelledby="sr-payroll">
              <h3 id="sr-payroll" className="text-sm font-semibold text-ink-2">
                {plan} payroll
              </h3>
              <p className="tabular mt-1 font-display text-5xl font-bold leading-none">{money(view.payroll)}</p>
              <p className={`tabular mt-2 text-sm font-semibold ${view.room >= 0 ? "text-good" : "text-bad"}`}>
                {view.room >= 0
                  ? `${money(view.room)} under the ${money(view.ev.cbt_threshold)} tax line`
                  : `${money(-view.room)} over the ${money(view.ev.cbt_threshold)} tax line`}
              </p>
              <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-ink-3">sWAR {lab.meta.stats_season}</dt>
                  <dd className="tabular font-semibold">{num(view.ev.war)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-3">Proj. {plan}</dt>
                  <dd className="tabular font-semibold">{num(view.ev.proj_war)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-3">Players</dt>
                  <dd className="tabular font-semibold">{view.ev.count}</dd>
                </div>
              </dl>
              {view.ev.expiring.length > 0 && (
                <p className="mt-3 text-xs text-ink-2">
                  <span className="tabular font-semibold">{view.ev.expiring.length}</span> contracts end after {plan}.
                </p>
              )}
            </section>

            <section aria-labelledby="sr-holes">
              <h3 id="sr-holes" className="text-sm font-semibold text-ink-2">
                Holes to fill <span className="tabular text-ink-3">{view.ev.needs.length}</span>
              </h3>
              {view.ev.needs.length === 0 ? (
                <p className="mt-2 text-sm text-ink-2">Every lineup slot and rotation spot is average or better.</p>
              ) : (
                <ul className="mt-2 divide-y divide-line">
                  {view.ev.needs.map((n) => (
                    <li key={`${n.slot}-${n.message}`} className="flex gap-3 py-2 text-sm">
                      <span className="tabular w-8 shrink-0 font-display text-lg font-bold leading-5">{n.slot}</span>
                      <span className="min-w-0">
                        <span className={`text-xs font-semibold ${n.severity === "empty" ? "text-bad" : "text-accent-text"}`}>
                          {SEVERITY_WORD[n.severity]}
                        </span>
                        <span className="block text-ink-2">{n.message.replace(new RegExp(`^${n.slot}:\\s*`), "")}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </aside>

          <div className="min-w-0">
            <h2 className="sr-only">{view.r.team.name} binder</h2>
            <section aria-labelledby="binder-lineup">
              <h3 id="binder-lineup" className="mb-3 flex items-baseline gap-2">
                <span className="font-display text-2xl font-bold">Lineup</span>
                <span className="text-sm text-ink-3">by position</span>
              </h3>
              <Sleeves label="Lineup">
                {view.lineup.map(({ slot, player }, i) => {
                  const sev = view.weak.get(slot);
                  return (
                    <li key={`${team}-${slot}`} className="flex flex-col gap-1.5">
                      <span className="flex items-baseline gap-2 text-xs">
                        <span className="font-semibold text-ink-2">{slot}</span>
                        {sev && (
                          <span className={`font-semibold ${sev === "empty" ? "text-bad" : "text-accent-text"}`}>
                            {sev === "empty" ? "Empty" : "Below average"}
                          </span>
                        )}
                      </span>
                      {player ? (
                        <PlayerCard
                          key={`${team}-${player.id}`}
                          player={player}
                          planSeason={plan}
                          statsSeason={lab.meta.stats_season}
                          onOpen={onOpen}
                          dealIndex={i}
                        />
                      ) : (
                        <EmptySleeve label={`No starter at ${slot}`} />
                      )}
                    </li>
                  );
                })}
              </Sleeves>
            </section>

            <BinderPage
              key={`rot-${team}`}
              title="Rotation"
              count={view.rotation.length}
              players={view.rotation}
              lab={lab}
              onOpen={onOpen}
              roleLabel={(i) => `SP${i + 1}`}
            />
            <BinderPage key={`pen-${team}`} title="Bullpen" count={view.bullpen.length} players={view.bullpen} lab={lab} onOpen={onOpen} />
            <BinderPage key={`bench-${team}`} title="Bench" count={view.bench.length} players={view.bench} lab={lab} onOpen={onOpen} />

            <section aria-labelledby="binder-ledger" className="mt-10">
              <h3 id="binder-ledger" className="mb-1 font-display text-2xl font-bold">
                Ledger
              </h3>
              <p className="mb-4 text-sm text-ink-2">Committed salary by season against the tax line. Biggest contracts are named.</p>
              <div className="rounded-lg border border-line bg-surface p-4">
                <PayrollLedger
                  players={view.r.players}
                  planSeason={plan}
                  cbt={view.ev.cbt_threshold}
                  onSelect={onOpen}
                />
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
