"use client";

import { useRef, useState, type ReactNode } from "react";
import { ControlPips } from "@/components/viz/ControlPips";
import { Fingerprint } from "@/components/viz/Fingerprint";
import { RatingBar } from "@/components/viz/RatingBar";
import { STATUS_LABEL, controlYears, handedness, money, num, positionLabel, rate, ratingKeys } from "@/lib/format";
import type { Player } from "@/lib/types";
import s from "./scouting.module.css";

export const CARD_SIZE = "h-[19rem] w-[12.5rem]";

export function planSalary(p: Player, planSeason: number): number | null {
  const y = p.contract.years.find((c) => c.year === planSeason);
  if (y) return y.salary;
  return p.contract.control_through >= planSeason ? p.contract.salary_now : null;
}

function keyStats(p: Player): [string, string][] {
  const st = p.stats;
  if (p.group === "hitter") {
    return [
      ["OPS", rate(st.ops)],
      ["HR", String(st.hr ?? 0)],
      ["sWAR", num(p.war)],
    ];
  }
  return [
    ["ERA", num(st.era, 2)],
    ["K%", num(st.k_pct)],
    ["sWAR", num(p.war)],
  ];
}

function FlipIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M2.5 8a5.5 5.5 0 0 1 9.6-3.7M13.5 8a5.5 5.5 0 0 1-9.6 3.7"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <path d="M12.4 1.8v2.8H9.6M3.6 14.2v-2.8h2.8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

interface Props {
  player: Player;
  planSeason: number;
  statsSeason: number;
  onOpen: (id: number) => void;
  /** Position in a freshly dealt group; the first 4 stagger in. Omit to skip the entrance. */
  dealIndex?: number;
  selected?: boolean;
  /** Rendered under the card, outside the flipping sheet (reasons, trade toggle…). */
  children?: ReactNode;
}

export function PlayerCard({ player: p, planSeason, statsSeason, onOpen, dealIndex, selected = false, children }: Props) {
  const [flipped, setFlipped] = useState(false);
  const frontRef = useRef<HTMLButtonElement>(null);
  const backRef = useRef<HTMLButtonElement>(null);
  const salary = planSalary(p, planSeason);
  const years = controlYears(p, planSeason);
  const pos = positionLabel(p);

  const turn = (toBack: boolean) => {
    setFlipped(toBack);
    // Keep focus on the visible face so keyboard users never land on an inert side.
    requestAnimationFrame(() => (toBack ? backRef.current : frontRef.current)?.focus({ preventScroll: true }));
  };

  const enter = dealIndex !== undefined;
  return (
    <div
      className={`flex w-[12.5rem] shrink-0 snap-start flex-col gap-2 ${enter ? s.enter : ""}`}
      style={enter ? { animationDelay: `${Math.min(dealIndex, 3) * 40}ms` } : undefined}
    >
      <div
        className={`${s.scene} ${CARD_SIZE} rounded-lg ${selected ? "ring-2 ring-accent ring-offset-2 ring-offset-bg" : ""}`}
      >
        <div className={`${s.sheet} ${flipped ? s.flipped : ""}`}>
          {/* Front */}
          <button
            ref={frontRef}
            type="button"
            inert={flipped}
            onClick={() => turn(true)}
            aria-label={`${p.name}, ${p.team} ${pos}, overall ${p.ovr}, potential ${p.pot}. Turn over for the scouting sheet`}
            className={`${s.face} flex flex-col rounded-lg border border-line bg-surface p-3 text-left transition-colors duration-fast ease-out hover:border-ink-3`}
          >
            <span className="flex w-full items-center gap-2 text-xs text-ink-2">
              <span className="tabular min-w-0 flex-1 truncate font-semibold">
                {p.team} · {pos} · Age {p.age}
              </span>
              <span className="text-ink-3">
                <FlipIcon />
              </span>
            </span>
            <span className="mt-1 block w-full truncate font-display text-[1.65rem] font-bold leading-tight" title={p.name}>
              {p.name}
            </span>
            <span className="block text-xs text-ink-3">{handedness(p)}</span>

            <span className="mt-2 flex flex-1 items-center gap-3">
              <Fingerprint group={p.group} ratings={p.ratings} size={88} />
              <span className="flex flex-col">
                <span className="tabular font-display text-6xl font-bold leading-none">{p.ovr}</span>
                <span className="mt-0.5 text-[11px] font-semibold text-ink-3">OVR</span>
                <span className="tabular mt-2 text-sm font-semibold text-ink-2">
                  {p.pot} <span className="text-[11px] text-ink-3">POT</span>
                </span>
              </span>
            </span>

            <span className="mt-2 block w-full border-t border-line pt-2">
              <span className="flex items-baseline gap-1.5">
                <span className="tabular text-base font-semibold">{salary === null ? "Free agent" : money(salary)}</span>
                {salary !== null && <span className="tabular text-xs text-ink-3">in {planSeason}</span>}
                {!p.contract.verified && (
                  <span
                    className="ml-auto rounded-sm border border-line px-1 text-[10px] font-semibold text-ink-2"
                    title="Salary is estimated from service time, not a reported contract"
                  >
                    Estimate
                  </span>
                )}
              </span>
              <span className="mt-1 flex min-w-0 items-center gap-2">
                <ControlPips player={p} planSeason={planSeason} max={6} />
                <span className="tabular min-w-0 truncate whitespace-nowrap text-[11px] text-ink-3">
                  {years > 0 ? `${years} yr${years === 1 ? "" : "s"} · ${STATUS_LABEL[p.contract.status]}` : ""}
                </span>
              </span>
            </span>
          </button>

          {/* Back: the 20-80 scouting sheet */}
          <section
            inert={!flipped}
            aria-label={`${p.name} scouting sheet`}
            className={`${s.face} ${s.back} flex flex-col rounded-lg border border-line bg-surface p-3`}
          >
            <div className="flex items-start gap-1">
              <div className="min-w-0 flex-1">
                <p className="truncate font-display text-xl font-bold leading-tight" title={p.name}>
                  {p.name}
                </p>
                <p className="text-[11px] text-ink-3">Scouting sheet · 20–80</p>
              </div>
              <button
                ref={backRef}
                type="button"
                onClick={() => turn(false)}
                aria-label={`Turn ${p.name} back to the front`}
                className="-mr-1.5 -mt-1.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded text-ink-2 transition-colors duration-fast ease-out hover:bg-surface-2 hover:text-ink"
              >
                <FlipIcon />
              </button>
            </div>

            <div className={`${s.bars} mt-1 space-y-1`}>
              {ratingKeys(p.group).map((k) => (
                <RatingBar key={k} rating={k} value={p.ratings[k]} compact />
              ))}
            </div>

            <dl className="mt-auto grid grid-cols-3 gap-2 border-t border-line pt-2">
              {keyStats(p).map(([k, v]) => (
                <div key={k}>
                  <dt className="text-[11px] text-ink-3">
                    {k === "sWAR" ? `sWAR ’${String(statsSeason).slice(2)}` : k}
                  </dt>
                  <dd className="tabular text-sm font-semibold">{v}</dd>
                </div>
              ))}
            </dl>

            <button
              type="button"
              onClick={() => onOpen(p.id)}
              className="mt-2 min-h-10 w-full rounded border border-line text-sm font-semibold text-ink transition-colors duration-fast ease-out hover:border-ink-3 hover:bg-surface-2"
            >
              View full report
            </button>
          </section>
        </div>
      </div>
      {children}
    </div>
  );
}

/** Dashed sleeve for a binder slot with no card in it. */
export function EmptySleeve({ label }: { label: string }) {
  return (
    <div
      className={`${CARD_SIZE} flex shrink-0 snap-start items-center justify-center rounded-lg border border-dashed border-line p-4 text-center text-sm text-ink-2`}
    >
      {label}
    </div>
  );
}
