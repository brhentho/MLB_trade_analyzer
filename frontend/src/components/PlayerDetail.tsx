"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  STATUS_LABEL,
  handedness,
  money,
  num,
  positionLabel,
  rate,
  ratingKeys,
  signedMoney,
} from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { Player, SimilarResult } from "@/lib/types";
import { ErrorState, LoadingRows } from "./States";
import { ControlPips } from "./viz/ControlPips";
import { Fingerprint } from "./viz/Fingerprint";
import { RatingBar } from "./viz/RatingBar";

interface Props {
  playerId: number;
  planSeason: number;
  statsSeason: number;
  archetypeLabels?: Record<string, string>;
  onSelectPlayer?: (id: number) => void;
  /** Optional slot for treatment-specific actions (add to roster, add to trade…). */
  actions?: (p: Player) => React.ReactNode;
}

function StatLine({ p, season }: { p: Player; season: number }) {
  const s = p.stats;
  const items: [string, string][] =
    p.group === "hitter"
      ? [
          ["PA", String(s.pa ?? 0)],
          ["AVG/OBP/SLG", `${rate(s.avg)}/${rate(s.obp)}/${rate(s.slg)}`],
          ["HR", String(s.hr ?? 0)],
          ["SB", String(s.sb ?? 0)],
          ["wOBA", rate(s.woba)],
          ["xwOBA", rate(s.xwoba)],
        ]
      : [
          ["IP", num(s.ip ?? 0)],
          ["ERA", num(s.era, 2)],
          ["FIP", num(s.fip, 2)],
          ["K%", num(s.k_pct)],
          ["BB%", num(s.bb_pct)],
          [p.role === "RP" ? "SV/HLD" : "W-L", p.role === "RP" ? `${s.sv ?? 0}/${s.hld ?? 0}` : `${s.w ?? 0}-${s.l ?? 0}`],
        ];
  return (
    <dl className="grid grid-cols-3 gap-x-3 gap-y-2 text-sm">
      <dt className="sr-only">Season</dt>
      <dd className="sr-only">{season}</dd>
      {items.map(([k, v]) => (
        <div key={k}>
          <dt className="text-xs text-ink-3">{k}</dt>
          <dd className="tabular font-semibold">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function PlayerDetail({ playerId, planSeason, statsSeason, archetypeLabels = {}, onSelectPlayer, actions }: Props) {
  const player = useAsync(() => api.player(playerId), [playerId]);
  const [comps, setComps] = useState<SimilarResult | null>(null);
  const [compsMode, setCompsMode] = useState<"any" | "cheaper">("any");
  const [compsBusy, setCompsBusy] = useState(false);

  if (player.status === "error") return <ErrorState message={player.error} onRetry={player.reload} />;
  if (!player.data) return <LoadingRows label="Loading player…" rows={8} />;
  const p = player.data;
  const c = p.contract;

  const loadComps = async (mode: "any" | "cheaper") => {
    setCompsMode(mode);
    setCompsBusy(true);
    try {
      setComps(
        await api.similar(p.id, {
          limit: 6,
          ...(mode === "cheaper" ? { salary_max: Math.max(1, c.salary_now * 0.6) } : {}),
        }),
      );
    } finally {
      setCompsBusy(false);
    }
  };

  return (
    <article className="space-y-5" aria-labelledby={`player-${p.id}`}>
      <header className="flex items-start gap-4">
        <Fingerprint group={p.group} ratings={p.ratings} size={112} labels />
        <div className="min-w-0 flex-1">
          <h2 id={`player-${p.id}`} className="truncate text-xl font-bold">
            {p.name}
          </h2>
          <p className="text-sm text-ink-2">
            {p.team} · {positionLabel(p)} · Age {p.age} · {handedness(p)}
          </p>
          <div className="mt-2 flex items-baseline gap-4">
            <span>
              <span className="tabular text-2xl font-bold">{p.ovr}</span>
              <span className="ml-1 text-xs text-ink-3">OVR</span>
            </span>
            <span>
              <span className="tabular text-lg font-semibold text-ink-2">{p.pot}</span>
              <span className="ml-1 text-xs text-ink-3">POT</span>
            </span>
            <span className="whitespace-nowrap">
              <span className="tabular text-lg font-semibold">{num(p.war)}</span>
              <span className="ml-1 text-xs text-ink-3">sWAR {statsSeason}</span>
            </span>
          </div>
          {p.archetypes.length > 0 && (
            <p className="mt-2 flex flex-wrap gap-1.5 text-xs">
              {p.archetypes.map((a) => (
                <span key={a} className="rounded-full border border-line px-2 py-0.5 text-ink-2">
                  {archetypeLabels[a] ?? a}
                </span>
              ))}
            </p>
          )}
        </div>
      </header>

      {actions && <div className="flex flex-wrap gap-2">{actions(p)}</div>}

      <section aria-label="Scouting ratings" className="space-y-1.5">
        <h3 className="text-xs font-semibold text-ink-3">Ratings (20–80, from {statsSeason} Statcast percentiles)</h3>
        {ratingKeys(p.group).map((k) => (
          <RatingBar key={k} rating={k} value={p.ratings[k]} exact />
        ))}
      </section>

      <section aria-label={`${statsSeason} stats`}>
        <h3 className="mb-2 text-xs font-semibold text-ink-3">{statsSeason} season</h3>
        <StatLine p={p} season={statsSeason} />
      </section>

      <section aria-label="Contract">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-ink-3">Contract</h3>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
              c.verified ? "bg-good/15 text-good" : "bg-surface-2 text-ink-2"
            }`}
          >
            {c.verified ? "Verified" : "Estimate"} · {STATUS_LABEL[c.status]}
          </span>
        </div>
        {c.signed && <p className="mb-2 text-sm">{c.signed}</p>}
        <div className="mb-2">
          <ControlPips player={p} planSeason={planSeason} max={12} />
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-ink-3">
              <th className="py-1 font-medium">Season</th>
              <th className="py-1 text-right font-medium">Salary</th>
              <th className="py-1 text-right font-medium">Proj. sWAR</th>
            </tr>
          </thead>
          <tbody className="tabular">
            {c.years.slice(0, 8).map((y, i) => (
              <tr key={y.year} className="border-t border-line">
                <td className="py-1">{y.year}</td>
                <td className="py-1 text-right">{money(y.salary)}</td>
                <td className="py-1 text-right">{num(p.proj_war[i])}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {c.years.length > 8 && <p className="mt-1 text-xs text-ink-3">+{c.years.length - 8} more seasons</p>}
        <p className="mt-2 text-sm">
          Surplus value <span className="tabular font-semibold">{signedMoney(p.surplus)}</span>
        </p>
        {c.notes && <p className="mt-1 text-xs text-ink-3">{c.notes}</p>}
      </section>

      <section aria-label="Comparable players">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h3 className="mr-auto text-xs font-semibold text-ink-3">Plays like</h3>
          <button
            type="button"
            onClick={() => loadComps("any")}
            className={`min-h-8 rounded border px-2 text-xs ${compsMode === "any" && comps ? "border-accent text-ink" : "border-line text-ink-2"}`}
          >
            Find comps
          </button>
          <button
            type="button"
            onClick={() => loadComps("cheaper")}
            className={`min-h-8 rounded border px-2 text-xs ${compsMode === "cheaper" && comps ? "border-accent text-ink" : "border-line text-ink-2"}`}
          >
            Cheaper comps
          </button>
        </div>
        {compsBusy && <LoadingRows label="Finding comparable players…" rows={3} />}
        {!compsBusy && comps && comps.results.length === 0 && (
          <p className="text-sm text-ink-2">No players with this shape at that price.</p>
        )}
        {!compsBusy && comps && comps.results.length > 0 && (
          <ul className="divide-y divide-line">
            {comps.results.map((r) => (
              <li key={r.player.id}>
                <button
                  type="button"
                  onClick={() => onSelectPlayer?.(r.player.id)}
                  className="flex w-full items-center gap-3 py-1.5 text-left text-sm hover:bg-surface-2"
                >
                  <Fingerprint group={r.player.group} ratings={r.player.ratings} compare={p.ratings} size={34} />
                  <span className="min-w-0 flex-1 truncate">
                    <span className="font-semibold">{r.player.name}</span>{" "}
                    <span className="text-ink-3">
                      {r.player.team} · {positionLabel(r.player)}
                    </span>
                  </span>
                  <span className="tabular text-xs text-ink-2">{r.similarity}% match</span>
                  <span className="tabular w-16 text-right text-xs">{signedMoney(r.salary_delta)}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
