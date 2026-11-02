"use client";

import { useState } from "react";
import { ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { TradeBalance } from "@/components/viz/TradeBalance";
import { api } from "@/lib/api";
import { money, num, signedMoney } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { Meta, Team, TradeEvaluation } from "@/lib/types";
import { PlayerTable } from "./PlayerTable";

interface Props {
  meta: Meta;
  teams: Team[];
  teamA: string;
  onSelect: (id: number) => void;
  selectedId: number | null;
}

function Side({
  team,
  setTeam,
  teams,
  picked,
  toggle,
  meta,
  id,
  onSelect,
  selectedId,
}: {
  team: string;
  setTeam: (t: string) => void;
  teams: Team[];
  picked: Set<number>;
  toggle: (id: number) => void;
  meta: Meta;
  id: string;
  onSelect: (id: number) => void;
  selectedId: number | null;
}) {
  const roster = useAsync(() => api.roster(team), [team]);
  return (
    <section aria-labelledby={`${id}-h`} className="min-w-0">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 id={`${id}-h`} className="text-sm font-semibold">
          {id === "side-a" ? "You send" : "You get"}
        </h2>
        <TeamPicker teams={teams} value={team} onChange={setTeam} id={`${id}-team`} label="from" />
      </div>
      {roster.status === "error" && <ErrorState message={roster.error} onRetry={roster.reload} />}
      {!roster.data && roster.status !== "error" && <LoadingRows label="Loading roster…" />}
      {roster.data && (
        <div className="max-h-[28rem] overflow-y-auto rounded border border-line">
          <PlayerTable
            group="hitter"
            players={roster.data.players}
            planSeason={meta.plan_season}
            caption={`${team} roster`}
            checked={picked}
            onToggle={toggle}
            onSelect={onSelect}
            selectedId={selectedId}
            compact
          />
        </div>
      )}
      <p className="mt-1 text-xs text-ink-3">
        <span className="tabular">{picked.size}</span> selected
      </p>
    </section>
  );
}

/** S5: build and grade a trade from two real rosters. */
export function TradeView({ meta, teams, teamA, onSelect, selectedId }: Props) {
  const [a, setA] = useState(teamA);
  const [b, setB] = useState(teams.find((t) => t.abbrev !== teamA)?.abbrev ?? "NYY");
  const [send, setSend] = useState<Set<number>>(new Set());
  const [get, setGet] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<TradeEvaluation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (set: Set<number>, update: (s: Set<number>) => void) => (id: number) => {
    const next = new Set(set);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    update(next);
    setResult(null);
  };

  const grade = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api.evaluateTrade({ team_a: a, team_b: b, team_a_receives: [...get], team_b_receives: [...send] }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const years = result ? Object.keys(result.payroll_delta_team_a).slice(0, 6) : [];

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <Side
          id="side-a"
          team={a}
          setTeam={(t) => {
            setA(t);
            setSend(new Set());
            setResult(null);
          }}
          teams={teams}
          picked={send}
          toggle={toggle(send, setSend)}
          meta={meta}
          onSelect={onSelect}
          selectedId={selectedId}
        />
        <Side
          id="side-b"
          team={b}
          setTeam={(t) => {
            setB(t);
            setGet(new Set());
            setResult(null);
          }}
          teams={teams}
          picked={get}
          toggle={toggle(get, setGet)}
          meta={meta}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={grade}
          disabled={busy || send.size === 0 || get.size === 0 || a === b}
          className="min-h-10 rounded bg-accent px-5 text-sm font-semibold text-accent-ink transition-opacity duration-fast ease-out disabled:opacity-50"
        >
          {busy ? "Grading…" : "Grade trade"}
        </button>
        <span className="text-xs text-ink-3">
          {a === b
            ? "Pick two different teams."
            : send.size === 0 || get.size === 0
              ? "Select at least one player on each side."
              : `${send.size} for ${get.size}`}
        </span>
      </div>

      {error && <ErrorState message={error} />}

      {result && (
        <section aria-labelledby="verdict-h" className="grid gap-6 border-t border-line pt-6 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <div className="space-y-4">
            <div className="flex items-baseline gap-4">
              <h2 id="verdict-h" className="sr-only">
                Trade grade
              </h2>
              <span className="font-mono text-5xl font-bold text-accent-text">{result.grade}</span>
              <span className="text-sm text-ink-2">
                Fairness <span className="tabular font-semibold text-ink">{result.fairness_score}</span>/100
              </span>
            </div>
            <TradeBalance
              leftLabel={result.team_a_name}
              rightLabel={result.team_b_name}
              left={result.team_a.surplus}
              right={result.team_b.surplus}
            />
            <table className="w-full text-sm">
              <caption className="mb-1 text-left text-xs font-semibold text-ink-3">
                Payroll change for {result.team_a_name}
              </caption>
              <tbody className="tabular">
                {years.map((y) => {
                  const d = result.payroll_delta_team_a[y] ?? 0;
                  return (
                    <tr key={y} className="border-t border-line">
                      <td className="py-1">{y}</td>
                      <td className={`py-1 text-right ${d > 0 ? "text-bad" : d < 0 ? "text-good" : ""}`}>
                        {signedMoney(d)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="space-y-4 text-sm">
            <p className="text-base">{result.summary}</p>
            <dl className="grid gap-4 md:grid-cols-2">
              {(["team_a", "team_b"] as const).map((side) => {
                const s = result[side];
                return (
                  <div key={side}>
                    <dt className="font-semibold">{side === "team_a" ? result.team_a_name : result.team_b_name}</dt>
                    <dd className="mt-1 text-ink-2">{side === "team_a" ? result.team_a_analysis : result.team_b_analysis}</dd>
                    <dd className="tabular mt-2 text-xs text-ink-3">
                      {signedMoney(s.surplus)} surplus · {num(s.proj_war_next)} proj. sWAR · {money(s.salary_now)} ·{" "}
                      {s.control_years} control yrs
                    </dd>
                  </div>
                );
              })}
            </dl>
            <div>
              <h3 className="text-xs font-semibold text-ink-3">Risks</h3>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-ink-2">
                {result.risks.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
            <p>
              <span className="font-semibold">Recommendation.</span> {result.recommendation}
            </p>
            <p className="text-xs text-ink-3">
              {result.narrative_source === "ai"
                ? "Narrative written by AI from the computed numbers above."
                : "Narrative written from rules; set OPENAI_API_KEY on the API for an AI write-up."}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
