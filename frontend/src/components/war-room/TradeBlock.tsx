"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { money, num, positionLabel } from "@/lib/format";
import type { Player, Team, TradeEvaluation } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { EmptyState, ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { TradeBalance } from "@/components/viz/TradeBalance";

export interface TradeState {
  out: number[];
  partner: string;
  incoming: number[];
}

interface Props {
  team: Team;
  teams: Team[];
  roster: Player[];
  trade: TradeState;
  onTrade: (t: TradeState) => void;
  aiAvailable: boolean;
}

function PickList({
  legend,
  players,
  picked,
  onToggle,
}: {
  legend: string;
  players: Player[];
  picked: number[];
  onToggle: (id: number) => void;
}) {
  const [q, setQ] = useState("");
  const rows = [...players]
    .sort((a, b) => b.war - a.war)
    .filter((p) => !q || p.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <fieldset className="min-w-0">
      <legend className="mb-1 text-xs font-semibold text-ink-3">
        {legend} <span className="tabular">({picked.length} picked)</span>
      </legend>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Filter by name"
        aria-label={`Filter ${legend.toLowerCase()} by name`}
        className="mb-1 min-h-9 w-full rounded border border-line bg-bg px-2 text-sm placeholder:text-ink-3"
      />
      <ul className="max-h-52 overflow-y-auto border-y border-line">
        {rows.map((p) => (
          <li key={p.id}>
            <label className="flex min-h-10 cursor-pointer items-center gap-2 px-1 text-sm hover:bg-surface-2">
              <input
                type="checkbox"
                checked={picked.includes(p.id)}
                onChange={() => onToggle(p.id)}
                className="h-4 w-4 accent-[rgb(var(--accent))]"
              />
              <span className="min-w-0 flex-1 truncate">
                {p.name} <span className="text-ink-3">{positionLabel(p)}</span>
              </span>
              <span className="tabular w-9 text-right text-xs">{num(p.war)}</span>
              <span className="tabular w-14 text-right text-xs text-ink-2">{money(p.contract.salary_now)}</span>
            </label>
          </li>
        ))}
        {rows.length === 0 && <li className="px-1 py-2 text-sm text-ink-3">No one matches “{q}”.</li>}
      </ul>
    </fieldset>
  );
}

const toggle = (list: number[], id: number) => (list.includes(id) ? list.filter((i) => i !== id) : [...list, id]);

/** Lightweight trade grader: actual rosters on both sides, graded by surplus value. */
export function TradeBlock({ team, teams, roster, trade, onTrade, aiAvailable }: Props) {
  const partnerRoster = useAsync(() => api.roster(trade.partner), [trade.partner]);
  const [result, setResult] = useState<TradeEvaluation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ready = trade.out.length > 0 && trade.incoming.length > 0;

  const grade = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api.evaluateTrade({
          team_a: team.abbrev,
          team_b: trade.partner,
          team_a_receives: trade.incoming,
          team_b_receives: trade.out,
          use_ai: aiAvailable,
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
        <PickList
          legend={`${team.short || team.abbrev} send`}
          players={roster}
          picked={trade.out}
          onToggle={(id) => onTrade({ ...trade, out: toggle(trade.out, id) })}
        />
        <div className="min-w-0 space-y-2">
          <TeamPicker
            id="war-room-partner"
            label="Trade with"
            teams={teams.filter((t) => t.abbrev !== team.abbrev)}
            value={trade.partner}
            onChange={(abbrev) => onTrade({ ...trade, partner: abbrev, incoming: [] })}
            className="w-full [&>select]:min-w-0 [&>select]:flex-1"
          />
          {partnerRoster.status === "error" ? (
            <ErrorState message={partnerRoster.error} onRetry={partnerRoster.reload} />
          ) : !partnerRoster.data || partnerRoster.data.team.abbrev !== trade.partner ? (
            <LoadingRows label="Loading partner roster…" rows={5} />
          ) : (
            <PickList
              legend={`${partnerRoster.data.team.short || trade.partner} send`}
              players={partnerRoster.data.players}
              picked={trade.incoming}
              onToggle={(id) => onTrade({ ...trade, incoming: toggle(trade.incoming, id) })}
            />
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={grade}
          disabled={!ready || busy}
          className="min-h-10 rounded bg-accent px-4 text-sm font-semibold text-accent-ink hover:bg-accent/90 disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-ink-3"
        >
          {busy ? "Grading trade…" : "Grade trade"}
        </button>
        {!ready && <span className="text-xs text-ink-3">Pick at least one player on each side.</span>}
      </div>

      {error && <ErrorState message={error} onRetry={grade} />}
      {!result && !error && ready && !busy && (
        <EmptyState title="Ready to grade">Grading compares surplus value, payroll and years of control.</EmptyState>
      )}
      {result && (
        <section aria-label="Trade grade" className={`space-y-3 ${busy ? "opacity-60" : ""}`}>
          <div className="flex items-baseline gap-3">
            <span className="font-display text-5xl font-bold leading-none">{result.grade}</span>
            <span className="tabular text-sm text-ink-2">Fairness {result.fairness_score}/100</span>
            <span className="ml-auto text-xs text-ink-3">
              {result.narrative_source === "ai" ? "Written by AI" : "Written from rules"}
            </span>
          </div>
          <TradeBalance
            leftLabel={result.team_a_name}
            rightLabel={result.team_b_name}
            left={result.team_a.surplus}
            right={result.team_b.surplus}
          />
          <p className="text-sm">{result.summary}</p>
          {result.recommendation && <p className="text-sm text-ink-2">{result.recommendation}</p>}
          {result.risks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-ink-3">Risks</h4>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink-2">
                {result.risks.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
