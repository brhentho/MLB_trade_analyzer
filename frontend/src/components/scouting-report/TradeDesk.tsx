"use client";

import { useMemo, useState } from "react";
import { ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { TradeBalance } from "@/components/viz/TradeBalance";
import { api } from "@/lib/api";
import { money, num, positionLabel, signedMoney } from "@/lib/format";
import type { Group, Player, TradeEvaluation, TradeSide } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import type { LabData } from "@/lib/useLabData";
import { PlayerCard, planSalary } from "./PlayerCard";

interface Props {
  lab: LabData;
  onOpen: (id: number) => void;
}

interface TrayProps {
  side: "a" | "b";
  lab: LabData;
  team: string;
  onTeam: (t: string) => void;
  selected: number[];
  onToggle: (p: Player) => void;
  onOpen: (id: number) => void;
}

function Tray({ side, lab, team, onTeam, selected, onToggle, onOpen }: TrayProps) {
  const [group, setGroup] = useState<Group>("hitter");
  const roster = useAsync(() => api.roster(team), [team]);
  const plan = lab.meta.plan_season;
  const players = useMemo(
    () => (roster.data?.players ?? []).filter((p) => p.group === group).sort((x, y) => y.ovr - x.ovr),
    [roster.data, group],
  );
  const chosen = (roster.data?.players ?? []).filter((p) => selected.includes(p.id));
  const label = side === "a" ? "Team A" : "Team B";
  const short = roster.data?.team.abbrev ?? team;

  return (
    <section aria-labelledby={`sr-tray-${side}`} className="min-w-0">
      <h3 id={`sr-tray-${side}`} className="sr-only">
        {label}: {short} sends
      </h3>
      <TeamPicker teams={lab.teams} value={team} onChange={onTeam} label={label} id={`sr-trade-team-${side}`} />

      <div className="mt-4 rounded-lg border border-line bg-surface p-4">
        <p className="flex items-baseline gap-2">
          <span className="font-display text-2xl font-bold">{short} sends</span>
          <span className="tabular text-sm text-ink-3">{chosen.length}</span>
        </p>
        {chosen.length === 0 ? (
          <p className="mt-2 text-sm text-ink-2">Pick cards from the {short} roster below.</p>
        ) : (
          <ul className="mt-2 divide-y divide-line">
            {chosen.map((p) => {
              const sal = planSalary(p, plan);
              return (
                <li key={p.id} className="flex items-center gap-3 py-1.5 text-sm">
                  <span className="tabular w-8 shrink-0 font-display text-2xl font-bold leading-none">{p.ovr}</span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-semibold" title={p.name}>
                      {p.name}
                    </span>
                    <span className="tabular block text-xs text-ink-2">
                      {positionLabel(p)} · Age {p.age} · {sal === null ? "Free agent" : `${money(sal)} in ${plan}`}
                      {!p.contract.verified && " · Estimate"}
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={() => onToggle(p)}
                    aria-label={`Take ${p.name} off the table`}
                    className="min-h-10 shrink-0 rounded px-3 text-sm font-semibold text-ink-2 transition-colors duration-fast ease-out hover:bg-surface-2 hover:text-ink"
                  >
                    Remove
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="mt-5 flex items-center gap-3">
        <h4 className="text-sm font-semibold text-ink-2">{short} roster</h4>
        <div role="radiogroup" aria-label={`${short} roster group`} className="ml-auto inline-flex rounded border border-line p-0.5">
          {(["hitter", "pitcher"] as const).map((g) => (
            <button
              key={g}
              type="button"
              role="radio"
              aria-checked={group === g}
              onClick={() => setGroup(g)}
              className={`min-h-9 rounded-sm px-3 text-sm font-semibold transition-colors duration-fast ease-out ${
                group === g ? "bg-ink text-surface" : "text-ink-2 hover:text-ink"
              }`}
            >
              {g === "hitter" ? "Hitters" : "Pitchers"}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3">
        {roster.status === "error" && <ErrorState message={roster.error} onRetry={roster.reload} />}
        {roster.status === "loading" && !roster.data && <LoadingRows label={`Loading the ${team} roster…`} rows={4} />}
        {roster.data && (
          <ul
            aria-label={`${short} ${group === "hitter" ? "hitters" : "pitchers"}`}
            aria-busy={roster.status === "loading"}
            className="-mx-1 flex snap-x scroll-px-1 gap-4 overflow-x-auto px-1 pb-3 pt-1"
          >
            {players.map((p) => {
              const on = selected.includes(p.id);
              return (
                <li key={`${team}-${p.id}`}>
                  <PlayerCard
                    player={p}
                    planSeason={plan}
                    statsSeason={lab.meta.stats_season}
                    onOpen={onOpen}
                    selected={on}
                  >
                    <button
                      type="button"
                      aria-pressed={on}
                      onClick={() => onToggle(p)}
                      className={`min-h-10 w-full rounded border text-sm font-semibold transition-colors duration-fast ease-out ${
                        on ? "border-ink bg-ink text-surface" : "border-line text-ink hover:border-ink-3"
                      }`}
                    >
                      <span className="block truncate px-2">{on ? `On the table` : `Send ${p.name.split(" ").slice(-1)[0]}`}</span>
                    </button>
                  </PlayerCard>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}

function SideReport({
  title,
  side,
  analysis,
  payroll,
  plan,
}: {
  title: string;
  side: TradeSide;
  analysis: string;
  payroll?: Record<string, number>;
  plan: number;
}) {
  const stats: [string, string][] = [
    ["Surplus", signedMoney(side.surplus)],
    [`Proj. sWAR ${plan}`, num(side.proj_war_next)],
    ["Control", `${side.control_years} yrs`],
    [`Salary ${plan}`, money(side.salary_now)],
  ];
  return (
    <section aria-label={title} className="min-w-0">
      <h4 className="font-display text-xl font-bold">{title}</h4>
      <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
        {stats.map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-ink-3">{k}</dt>
            <dd className="tabular font-semibold">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-sm leading-relaxed">{analysis}</p>
      {payroll && Object.keys(payroll).length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-ink-3">Payroll change by season</p>
          <ul className="tabular mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
            {Object.entries(payroll)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(([y, d]) => (
                <li key={y}>
                  <span className="text-ink-3">{y}</span>{" "}
                  <span className={`font-semibold ${d > 0 ? "text-bad" : d < 0 ? "text-good" : ""}`}>{signedMoney(d)}</span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function TradeResult({ t, lab, stale, aShort, bShort }: { t: TradeEvaluation; lab: LabData; stale: boolean; aShort: string; bShort: string }) {
  const plan = lab.meta.plan_season;
  const winnerText =
    t.winner === "even" ? "Even deal" : `${t.winner === "team_a" ? t.team_a_name : t.team_b_name} win by ${money(Math.abs(t.surplus_diff))}`;
  const invertDelta = Object.fromEntries(Object.entries(t.payroll_delta_team_a).map(([y, d]) => [y, -d]));
  return (
    <article aria-labelledby="sr-trade-grade" className={`transition-opacity duration-base ease-out ${stale ? "opacity-60" : ""}`}>
      {stale && (
        <p role="status" className="mb-4 text-sm font-semibold text-ink-2">
          The cards on the table changed. Grade the trade again to update this report.
        </p>
      )}
      <div className="grid items-center gap-6 md:grid-cols-[auto_1fr_minmax(16rem,22rem)]">
        <div className="flex items-baseline gap-3">
          <span id="sr-trade-grade" className="font-display text-8xl font-bold leading-none" aria-label={`Grade ${t.grade}`}>
            {t.grade}
          </span>
        </div>
        <div className="min-w-0">
          <p className="text-lg font-semibold">{winnerText}</p>
          <p className="tabular text-sm text-ink-2">Fairness {t.fairness_score} out of 100</p>
          <p className="mt-2 text-xs font-semibold text-ink-3">
            {t.narrative_source === "ai" ? "Written by AI from the numbers below" : "Written from rules, not AI"}
          </p>
        </div>
        <TradeBalance leftLabel={aShort} rightLabel={bShort} left={t.team_a.surplus} right={t.team_b.surplus} />
      </div>

      <p className="mt-6 max-w-3xl text-lg leading-relaxed">{t.summary}</p>

      <div className="mt-8 grid gap-8 md:grid-cols-2">
        <SideReport
          title={`${t.team_a_name} receive`}
          side={t.team_a}
          analysis={t.team_a_analysis}
          payroll={t.payroll_delta_team_a}
          plan={plan}
        />
        <SideReport title={`${t.team_b_name} receive`} side={t.team_b} analysis={t.team_b_analysis} payroll={invertDelta} plan={plan} />
      </div>

      <div className="mt-8 grid gap-8 md:grid-cols-2">
        <section aria-labelledby="sr-trade-risks">
          <h4 id="sr-trade-risks" className="text-sm font-semibold text-ink-2">
            Risks <span className="tabular text-ink-3">{t.risks.length}</span>
          </h4>
          {t.risks.length === 0 ? (
            <p className="mt-2 text-sm text-ink-2">No contract or projection risks flagged.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {t.risks.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </section>
        <section aria-labelledby="sr-trade-rec">
          <h4 id="sr-trade-rec" className="text-sm font-semibold text-ink-2">
            Recommendation
          </h4>
          <p className="mt-2 text-base font-semibold">{t.recommendation}</p>
        </section>
      </div>
    </article>
  );
}

export function TradeDesk({ lab, onOpen }: Props) {
  const [teamA, setTeamA] = useState("SEA");
  const [teamB, setTeamB] = useState("NYY");
  const [sendA, setSendA] = useState<number[]>([]);
  const [sendB, setSendB] = useState<number[]>([]);
  const [grade, setGrade] = useState<{
    status: "idle" | "loading" | "ready" | "error";
    data: TradeEvaluation | null;
    error: string | null;
    key: string;
  }>({ status: "idle", data: null, error: null, key: "" });

  const key = `${teamA}:${[...sendA].sort().join(",")}|${teamB}:${[...sendB].sort().join(",")}`;
  const sameTeam = teamA === teamB;
  const ready = !sameTeam && sendA.length > 0 && sendB.length > 0;
  const hint = sameTeam
    ? "Pick two different teams."
    : sendA.length === 0 && sendB.length === 0
      ? "Put at least one card on the table from each side."
      : sendA.length === 0
        ? `Add a card from ${teamA}.`
        : sendB.length === 0
          ? `Add a card from ${teamB}.`
          : `${sendA.length} for ${sendB.length}`;

  const toggle = (set: React.Dispatch<React.SetStateAction<number[]>>) => (p: Player) =>
    set((ids) => (ids.includes(p.id) ? ids.filter((i) => i !== p.id) : [...ids, p.id]));

  const run = async () => {
    if (!ready) return;
    setGrade((g) => ({ ...g, status: "loading", error: null }));
    try {
      const data = await api.evaluateTrade({ team_a: teamA, team_b: teamB, team_a_receives: sendB, team_b_receives: sendA });
      setGrade({ status: "ready", data, error: null, key });
    } catch (e) {
      setGrade((g) => ({ ...g, status: "error", error: e instanceof Error ? e.message : String(e) }));
    }
  };

  return (
    <div>
      <div className="grid gap-10 lg:grid-cols-2">
        <Tray
          side="a"
          lab={lab}
          team={teamA}
          onTeam={(t) => {
            setTeamA(t);
            setSendA([]);
          }}
          selected={sendA}
          onToggle={toggle(setSendA)}
          onOpen={onOpen}
        />
        <Tray
          side="b"
          lab={lab}
          team={teamB}
          onTeam={(t) => {
            setTeamB(t);
            setSendB([]);
          }}
          selected={sendB}
          onToggle={toggle(setSendB)}
          onOpen={onOpen}
        />
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4 border-t border-line pt-6">
        <button
          type="button"
          onClick={() => void run()}
          disabled={!ready || grade.status === "loading"}
          className="min-h-11 rounded bg-accent px-6 text-base font-semibold text-accent-ink transition-opacity duration-fast ease-out disabled:opacity-50"
        >
          {grade.status === "loading" ? "Grading…" : "Grade trade"}
        </button>
        <p className="tabular text-sm text-ink-2" aria-live="polite">
          {hint}
        </p>
      </div>

      <div className="mt-8" aria-live="polite">
        {grade.status === "error" && <ErrorState message={grade.error ?? "The trade could not be graded."} onRetry={() => void run()} />}
        {grade.status === "loading" && !grade.data && <LoadingRows label="Grading the trade…" rows={4} />}
        {grade.data && grade.status !== "error" && <TradeResult t={grade.data} lab={lab} stale={grade.key !== key} aShort={grade.key.split(":")[0] ?? teamA} bShort={grade.key.split("|")[1]?.split(":")[0] ?? teamB} />}
      </div>
    </div>
  );
}
