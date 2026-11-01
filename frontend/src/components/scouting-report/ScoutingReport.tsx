"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useRef, useState, type KeyboardEvent } from "react";
import { ErrorState, LoadingRows } from "@/components/States";
import { useLabData } from "@/lib/useLabData";
import { DetailSheet } from "./DetailSheet";
import { NicheFinder } from "./NicheFinder";
import { TeamBinder } from "./TeamBinder";
import { TradeDesk } from "./TradeDesk";

const TABS = [
  { id: "team", label: "Take over a team", lede: "Your roster as a binder of cards. Turn any card over for its 20–80 scouting sheet." },
  { id: "find", label: "Find a niche player", lede: "Describe the player you need. Every card says why it matched." },
  { id: "trade", label: "Grade a trade", lede: "Put cards on the table from both teams, then grade the swap." },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function ScoutingReport() {
  const lab = useLabData();
  const [tab, setTab] = useState<TabId>("team");
  const [visited, setVisited] = useState<Set<TabId>>(() => new Set<TabId>(["team"]));
  const [detail, setDetail] = useState<number | null>(null);
  const tabRefs = useRef<Partial<Record<TabId, HTMLButtonElement | null>>>({});

  const select = (id: TabId, focus = false) => {
    setTab(id);
    setVisited((v) => (v.has(id) ? v : new Set(v).add(id)));
    if (focus) tabRefs.current[id]?.focus();
  };

  const onTabKey = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const n = TABS.length;
    const to =
      e.key === "ArrowRight" ? (i + 1) % n : e.key === "ArrowLeft" ? (i - 1 + n) % n : e.key === "Home" ? 0 : e.key === "End" ? n - 1 : -1;
    const next = TABS[to];
    if (!next) return;
    e.preventDefault();
    select(next.id, true);
  };

  const closeDetail = useCallback(() => setDetail(null), []);
  const current = TABS.find((t) => t.id === tab) ?? TABS[0];

  return (
    <div data-theme="paper" className="min-h-screen bg-bg text-ink">
      <div className="mx-auto max-w-[90rem] px-4 pb-20 pt-6 sm:px-8">
        <header className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <Link href="/" className="inline-flex min-h-10 items-center gap-3 rounded" aria-label="StatSlugger home">
            <Image src="/brand/logo.png" alt="" width={40} height={40} className="rounded" priority />
            <span className="font-display text-2xl font-bold tracking-tight">StatSlugger</span>
          </Link>
          <span className="text-sm text-ink-2">Scouting report</span>
          {lab.data && (
            <span className="tabular ml-auto text-xs text-ink-2">
              Planning {lab.data.meta.plan_season} · stats from {lab.data.meta.stats_season}
            </span>
          )}
        </header>

        <div role="tablist" aria-label="Front office tasks" className="mt-6 flex gap-1 overflow-x-auto border-b border-line">
          {TABS.map((t, i) => {
            const on = t.id === tab;
            return (
              <button
                key={t.id}
                ref={(el) => {
                  tabRefs.current[t.id] = el;
                }}
                id={`sr-tab-${t.id}`}
                type="button"
                role="tab"
                aria-selected={on}
                aria-controls={`sr-panel-${t.id}`}
                tabIndex={on ? 0 : -1}
                onClick={() => select(t.id)}
                onKeyDown={(e) => onTabKey(e, i)}
                className={`relative min-h-11 shrink-0 whitespace-nowrap px-2 text-sm font-semibold transition-colors duration-fast ease-out sm:px-3 ${
                  on ? "text-ink" : "text-ink-2 hover:text-ink"
                }`}
              >
                {t.label}
                <span
                  aria-hidden
                  className={`absolute inset-x-2 bottom-0 h-0.5 origin-left bg-ink transition-transform duration-base ease-out sm:inset-x-3 ${on ? "scale-x-100" : "scale-x-0"}`}
                />
              </button>
            );
          })}
        </div>

        <h1 className="mt-6 font-display text-4xl font-bold leading-tight sm:text-5xl">{current.label}</h1>
        <p className="mt-1 max-w-2xl text-ink-2">{current.lede}</p>

        <div className="mt-8">
          {lab.status === "error" && !lab.data && <ErrorState message={lab.error} onRetry={lab.reload} />}
          {!lab.data && lab.status === "loading" && <LoadingRows label="Opening the front office…" rows={6} />}
          {lab.data &&
            TABS.map((t) => (
              <div
                key={t.id}
                id={`sr-panel-${t.id}`}
                role="tabpanel"
                aria-labelledby={`sr-tab-${t.id}`}
                hidden={t.id !== tab}
              >
                {visited.has(t.id) && lab.data && (
                  <>
                    {t.id === "team" && <TeamBinder lab={lab.data} onOpen={setDetail} />}
                    {t.id === "find" && <NicheFinder lab={lab.data} onOpen={setDetail} />}
                    {t.id === "trade" && <TradeDesk lab={lab.data} onOpen={setDetail} />}
                  </>
                )}
              </div>
            ))}
        </div>

        <p className="mt-16 max-w-3xl text-xs text-ink-2">
          Ratings, sWAR and surplus value are StatSlugger estimates from MLB Stats API and Baseball Savant data. Salaries
          marked Estimate are derived from service time, not reported contracts.
        </p>
      </div>

      {lab.data && (
        <DetailSheet
          playerId={detail}
          planSeason={lab.data.meta.plan_season}
          statsSeason={lab.data.meta.stats_season}
          archetypeLabels={lab.data.archetypeLabels}
          onSelectPlayer={setDetail}
          onClose={closeDetail}
        />
      )}
    </div>
  );
}
