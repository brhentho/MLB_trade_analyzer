"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { PlayerDetail } from "@/components/PlayerDetail";
import { ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { RosterView } from "@/components/front-office/RosterView";
import { ScoutView } from "@/components/front-office/ScoutView";
import { TradeView } from "@/components/front-office/TradeView";
import { useLabData } from "@/lib/useLabData";

const TABS = [
  { id: "roster", label: "Roster" },
  { id: "scout", label: "Scout" },
  { id: "trade", label: "Trade" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export default function FrontOfficePage() {
  const lab = useLabData();
  const [team, setTeam] = useState("SEA");
  const [tab, setTab] = useState<Tab>("roster");
  const [selected, setSelected] = useState<number | null>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  const select = (id: number) => {
    returnFocus.current = document.activeElement as HTMLElement | null;
    setSelected(id);
  };
  const close = () => {
    setSelected(null);
    returnFocus.current?.focus();
  };

  useEffect(() => {
    if (selected === null) return;
    closeRef.current?.focus({ preventScroll: true });
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  const onTabKey = (e: React.KeyboardEvent, i: number) => {
    const delta = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!delta) return;
    const next = TABS[(i + delta + TABS.length) % TABS.length]!;
    setTab(next.id);
    document.getElementById(`tab-${next.id}`)?.focus();
  };

  return (
    <div data-theme="terminal" className="min-h-screen bg-bg text-ink">
      <header className="sticky top-0 z-30 border-b border-line bg-surface">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2">
          <Link href="/" className="font-mono text-sm font-bold tracking-tight">
            StatSlugger <span className="font-normal text-ink-3">front office</span>
          </Link>
          <div role="tablist" aria-label="Front office views" className="flex gap-1">
            {TABS.map((t, i) => (
              <button
                key={t.id}
                id={`tab-${t.id}`}
                role="tab"
                aria-selected={tab === t.id}
                aria-controls={`panel-${t.id}`}
                tabIndex={tab === t.id ? 0 : -1}
                onClick={() => setTab(t.id)}
                onKeyDown={(e) => onTabKey(e, i)}
                className={`min-h-10 rounded px-3 text-sm font-semibold transition-colors duration-fast ease-out ${
                  tab === t.id ? "bg-surface-2 text-ink" : "text-ink-3 hover:text-ink"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          {lab.data && (
            <TeamPicker teams={lab.data.teams} value={team} onChange={setTeam} label="Your club" className="ml-auto" />
          )}
          {lab.data && (
            <span className="tabular text-xs text-ink-3">
              Planning {lab.data.meta.plan_season} · stats {lab.data.meta.stats_season}
            </span>
          )}
        </div>
      </header>

      <div className={`grid ${selected !== null ? "lg:grid-cols-[minmax(0,1fr)_26rem]" : ""}`}>
        <main className="min-w-0 px-4 py-5">
          {lab.status === "error" && <ErrorState message={lab.error} onRetry={lab.reload} />}
          {!lab.data && lab.status !== "error" && <LoadingRows label="Loading league data…" rows={12} />}
          {lab.data && (
            <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
              {tab === "roster" && <RosterView team={team} meta={lab.data.meta} selectedId={selected} onSelect={select} />}
              {tab === "scout" && (
                <ScoutView
                  meta={lab.data.meta}
                  archetypes={lab.data.archetypes}
                  archetypeLabels={lab.data.archetypeLabels}
                  selectedId={selected}
                  onSelect={select}
                />
              )}
              {tab === "trade" && (
                <TradeView meta={lab.data.meta} teams={lab.data.teams} teamA={team} onSelect={select} selectedId={selected} />
              )}
            </div>
          )}
        </main>

        {selected !== null && lab.data && (
          <aside
            aria-label="Player report"
            className="fixed inset-0 z-40 overflow-y-auto bg-surface p-5 lg:sticky lg:top-[57px] lg:z-auto lg:h-[calc(100vh-57px)] lg:border-l lg:border-line"
          >
            <div className="mb-3 flex justify-end">
              <button
                ref={closeRef}
                type="button"
                onClick={close}
                className="min-h-10 rounded border border-line px-3 text-sm text-ink-2 hover:text-ink"
              >
                Close report
              </button>
            </div>
            <PlayerDetail
              key={selected}
              playerId={selected}
              planSeason={lab.data.meta.plan_season}
              statsSeason={lab.data.meta.stats_season}
              archetypeLabels={lab.data.archetypeLabels}
              onSelectPlayer={setSelected}
            />
          </aside>
        )}
      </div>
    </div>
  );
}
