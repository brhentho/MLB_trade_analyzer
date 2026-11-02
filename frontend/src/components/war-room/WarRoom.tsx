"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { LINEUP_ORDER, positionLabel } from "@/lib/format";
import type { AnyPlayer, Group, Player, Team, TeamRoster } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { type LabData, useLabData } from "@/lib/useLabData";
import { ErrorState, LoadingRows } from "@/components/States";
import { TeamPicker } from "@/components/TeamPicker";
import { Diamond } from "@/components/viz/Diamond";
import { PayrollLedger } from "@/components/viz/PayrollLedger";
import { DetailPanel } from "./DetailPanel";
import { DugoutRails } from "./DugoutRails";
import { Scoreboard } from "./Scoreboard";
import { ShapeDrawer } from "./ShapeDrawer";
import { SkillMap, type Source } from "./SkillMap";
import { SlotToken } from "./SlotToken";
import { TradeBlock, type TradeState } from "./TradeBlock";
import { type Sandbox, isLineupSlot, targetLabel, useSandbox } from "./useSandbox";

type Tab = "map" | "shape" | "trade";
const TABS: { id: Tab; label: string }[] = [
  { id: "map", label: "Skill map" },
  { id: "shape", label: "Draw a shape" },
  { id: "trade", label: "Trade block" },
];

const DEFAULT_TEAM = "SEA";

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => entry && setWidth(entry.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

const defaultSlot = (p: AnyPlayer) => {
  if ((LINEUP_ORDER as readonly string[]).includes(p.position)) return p.position;
  if (p.position === "OF") return "CF";
  return "DH";
};

export function WarRoom() {
  const lab = useLabData();
  const [team, setTeam] = useState(DEFAULT_TEAM);
  const roster = useAsync(() => api.roster(team), [team]);
  const teamName = lab.data?.teams.find((t) => t.abbrev === team)?.name ?? team;

  return (
    <div data-theme="warroom" className="min-h-screen bg-bg text-ink">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <div className="mr-auto min-w-0">
            <p className="text-xs text-ink-3">StatSlugger</p>
            <h1 className="font-display text-2xl font-bold leading-none tracking-wide">Diamond war room</h1>
          </div>
          {lab.data && (
            <TeamPicker teams={lab.data.teams} value={team} onChange={setTeam} label="Take over" id="war-room-team" />
          )}
        </div>
      </header>

      {lab.status === "error" && !lab.data ? (
        <main className="mx-auto max-w-3xl px-4 py-8">
          <ErrorState message={lab.error} onRetry={lab.reload} />
        </main>
      ) : roster.status === "error" ? (
        <main className="mx-auto max-w-3xl px-4 py-8">
          <ErrorState message={roster.error} onRetry={roster.reload} />
        </main>
      ) : !lab.data || !roster.data || roster.data.team.abbrev !== team ? (
        <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6">
          <LoadingRows label={`Loading ${teamName} roster…`} rows={10} />
        </main>
      ) : (
        <Room key={team} roster={roster.data} lab={lab.data} />
      )}
    </div>
  );
}

function Room({ roster, lab }: { roster: TeamRoster; lab: LabData }) {
  const { meta, teams, archetypes, archetypeLabels } = lab;
  const sandbox = useSandbox(roster);
  const [armed, setArmed] = useState<AnyPlayer | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const opener = useRef<Element | null>(null);
  const [tab, setTab] = useState<Tab>("map");
  const [group, setGroup] = useState<Group>("hitter");
  const [source, setSource] = useState<Source>(null);
  const searchSeq = useRef(0);
  const [trade, setTrade] = useState<TradeState>({
    out: [],
    partner: teams.find((t) => t.abbrev !== roster.team.abbrev && t.abbrev === "NYY")?.abbrev ??
      teams.find((t) => t.abbrev !== roster.team.abbrev)?.abbrev ?? "",
    incoming: [],
  });
  const mapPlayers = useAsync(() => api.players({ group, mapped: true }), [group]);
  const [diamondRef, diamondWidth] = useWidth<HTMLDivElement>();
  const compact = diamondWidth > 0 && diamondWidth < 600;

  const { current, cache } = sandbox;
  const onRoster = new Set(sandbox.ids);

  const openDetail = useCallback((id: number, el?: Element | null) => {
    opener.current = el ?? document.activeElement;
    setDetailId(id);
  }, []);

  const closeDetail = useCallback(() => {
    setDetailId(null);
    const el = opener.current;
    requestAnimationFrame(() => {
      if (el instanceof HTMLElement && el.isConnected) el.focus();
    });
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (detailId !== null) closeDetail();
      else if (armed) setArmed(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [armed, closeDetail, detailId]);

  const pick = (p: AnyPlayer, el: HTMLElement | null) => {
    setArmed(p);
    openDetail(p.id, el);
  };

  const put = async (p: AnyPlayer, target: string) => {
    setArmed(null);
    if (window.matchMedia("(max-width: 1023px)").matches) setDetailId(null);
    await sandbox.place(p, target);
  };

  const findReplacement = (slot: string) => {
    const pitch = slot === "SP" || slot === "RP";
    const label = pitch ? `Best available ${slot === "SP" ? "starters" : "relievers"}` : `Best available at ${slot}`;
    const filters = pitch
      ? { group: "pitcher" as const, roles: [slot as "SP" | "RP"] }
      : slot === "DH"
        ? { group: "hitter" as const }
        : { group: "hitter" as const, positions: ["LF", "CF", "RF"].includes(slot) ? [slot, "OF"] : [slot] };
    const id = ++searchSeq.current;
    const retry = () => findReplacement(slot);
    setTab("map");
    setGroup(pitch ? "pitcher" : "hitter");
    setSource({ kind: "search", label, status: "loading", players: [] });
    api.search({ ...filters, sort: "war", descending: true, limit: 40 }).then(
      (r) => {
        if (id !== searchSeq.current) return;
        setSource({
          kind: "search",
          label,
          status: "ready",
          players: r.results.map((x) => x.player).filter((p) => p.team !== roster.team.abbrev),
        });
      },
      (e: unknown) =>
        id === searchSeq.current &&
        setSource({ kind: "search", label, status: "error", players: [], error: e instanceof Error ? e.message : String(e), retry }),
    );
  };

  const onSlot = (slot: string, el: HTMLElement) => {
    if (armed && armed.group === "hitter") {
      void put(armed, slot);
      return;
    }
    const occ = current.depth.lineup[slot];
    if (occ != null) openDetail(occ, el);
    else findReplacement(slot);
  };

  const armedHitter = armed && armed.group === "hitter" ? armed.name : null;
  const last = sandbox.last;
  const lastName = last ? (cache[last.playerId]?.name ?? "Player") : "";
  const removedName = last?.removedId != null ? (cache[last.removedId]?.name ?? "A player") : null;
  const lastMessage = last
    ? last.landed === last.target
      ? `Put ${lastName} at ${targetLabel(last.target)}.${removedName ? ` ${removedName} came off the roster.` : ""}`
      : `${lastName} joined the roster, but the depth chart put him at ${targetLabel(last.landed)}${
          isLineupSlot(last.target) ? ` (it starts the best fit at ${last.target})` : ""
        }.${removedName ? ` ${removedName} came off the roster.` : ""}`
    : null;

  const roleNeeds = current.needs.filter((n) => !isLineupSlot(n.slot));
  const slotNeeds = current.needs.filter((n) => isLineupSlot(n.slot));

  const tabsRef = useRef<HTMLDivElement>(null);
  const onTabKey = (e: React.KeyboardEvent) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = TABS.findIndex((t) => t.id === tab);
    const next = TABS[(i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length];
    if (!next) return;
    setTab(next.id);
    tabsRef.current?.querySelector<HTMLButtonElement>(`#tab-${next.id}`)?.focus();
  };

  return (
    <>
      <main className="mx-auto grid max-w-[1600px] gap-x-8 gap-y-8 px-4 py-5 sm:px-6 lg:grid-cols-[minmax(0,1fr)_26rem] xl:grid-cols-[minmax(0,1fr)_30rem]">
        <section aria-labelledby="roster-heading" className="min-w-0 space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 id="roster-heading" className="font-display text-xl font-bold tracking-wide">
              {roster.team.name}
              {sandbox.changed && <span className="ml-2 text-sm font-semibold text-ink-3">working roster</span>}
            </h2>
            <button
              type="button"
              onClick={() => {
                sandbox.reset();
                setArmed(null);
              }}
              disabled={!sandbox.changed}
              className="min-h-10 rounded border border-line px-3 text-sm font-semibold hover:bg-surface-2 disabled:cursor-not-allowed disabled:text-ink-3 disabled:hover:bg-transparent"
            >
              Reset to actual roster
            </button>
          </div>
          <Scoreboard
            current={current}
            original={sandbox.original}
            changed={sandbox.changed}
            planSeason={meta.plan_season}
            statsSeason={meta.stats_season}
          />

          <Guide armed={armed} busy={sandbox.busy} message={lastMessage} onCancel={() => setArmed(null)} />
          {sandbox.error && <ErrorState message={sandbox.error} onRetry={sandbox.retry} />}

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_14rem]">
            <div className="min-w-0">
              <div ref={diamondRef} className="mx-auto max-w-[44rem] pb-2">
                <Diamond
                  ariaLabel={`${roster.team.name} lineup by position`}
                  renderSlot={(slot) => {
                    const id = current.depth.lineup[slot] ?? null;
                    const p = id != null ? (cache[id] ?? null) : null;
                    return (
                      <SlotToken
                        slot={slot}
                        player={p}
                        need={slotNeeds.find((n) => n.slot === slot)}
                        armedName={armedHitter}
                        compact={compact}
                        settle={!!last && last.landed === slot && last.playerId === id}
                        disabled={sandbox.busy}
                        onActivate={() => {
                          const el = document.activeElement;
                          onSlot(slot, el instanceof HTMLElement ? el : document.body);
                        }}
                      />
                    );
                  }}
                />
              </div>
              <Needs needs={current.needs} cache={cache} lineup={current.depth.lineup} onFind={findReplacement} />
            </div>
            <DugoutRails
              rotation={current.depth.rotation}
              bullpen={current.depth.bullpen}
              bench={current.depth.bench}
              players={cache}
              needs={roleNeeds}
              armed={armed}
              settleId={last && (last.landed === "rotation" || last.landed === "bullpen") ? last.playerId : null}
              disabled={sandbox.busy}
              onPut={(t) => armed && void put(armed, t)}
              onOpen={(id, el) => openDetail(id, el)}
            />
          </div>

          {sandbox.changed && <Moves sandbox={sandbox} onOpen={openDetail} />}
        </section>

        <section
          aria-label="Find players"
          className="min-w-0 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:self-start lg:overflow-y-auto lg:pr-1"
        >
          <div ref={tabsRef} role="tablist" aria-label="Ways to find players" className="flex border-b border-line" onKeyDown={onTabKey}>
            {TABS.map((t) => {
              const on = t.id === tab;
              return (
                <button
                  key={t.id}
                  id={`tab-${t.id}`}
                  type="button"
                  role="tab"
                  aria-selected={on}
                  aria-controls={`panel-${t.id}`}
                  tabIndex={on ? 0 : -1}
                  onClick={() => setTab(t.id)}
                  className={`-mb-px min-h-11 border-b-2 px-3 font-display text-base font-bold tracking-wide transition-colors duration-fast ease-out ${
                    on ? "border-ink text-ink" : "border-transparent text-ink-3 hover:text-ink-2"
                  }`}
                >
                  {t.label}
                  {t.id === "trade" && trade.out.length + trade.incoming.length > 0 && (
                    <span className="tabular ml-1 text-sm text-ink-3">{trade.out.length + trade.incoming.length}</span>
                  )}
                </button>
              );
            })}
          </div>
          <div id={`panel-${tab}`} role="tabpanel" aria-labelledby={`tab-${tab}`} className="space-y-3 pt-3">
            {tab !== "trade" && (
              <div role="group" aria-label="Player type" className="inline-flex rounded border border-line p-0.5">
                {(["hitter", "pitcher"] as const).map((g) => (
                  <button
                    key={g}
                    type="button"
                    aria-pressed={group === g}
                    onClick={() => {
                      setGroup(g);
                      setSource(null);
                    }}
                    className={`min-h-9 rounded-sm px-3 text-sm font-semibold ${
                      group === g ? "bg-surface-2 text-ink" : "text-ink-2 hover:text-ink"
                    }`}
                  >
                    {g === "hitter" ? "Hitters" : "Pitchers"}
                  </button>
                ))}
              </div>
            )}
            {tab === "map" && (
              <SkillMap
                group={group}
                players={mapPlayers}
                archetypes={archetypes}
                source={source}
                onSource={setSource}
                onRoster={onRoster}
                armedId={armed?.id ?? null}
                onPick={pick}
              />
            )}
            {tab === "shape" && <ShapeDrawer group={group} onRoster={onRoster} armedId={armed?.id ?? null} onPick={pick} />}
            {tab === "trade" && (
              <TradeBlock
                team={roster.team}
                teams={teams}
                roster={roster.players}
                trade={trade}
                onTrade={setTrade}
                aiAvailable={meta.ai_available}
              />
            )}
          </div>
        </section>

        <section aria-labelledby="ledger-heading" className="min-w-0 lg:col-span-2">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="ledger-heading" className="font-display text-xl font-bold tracking-wide">
              Payroll ledger
            </h2>
            <p className="text-xs text-ink-3">
              Committed salary by season{sandbox.added.length > 0 ? "; your additions are highlighted" : ""}. Lighter
              segments are estimates.
            </p>
          </div>
          {sandbox.players.length === 0 ? (
            <p className="text-sm text-ink-3">No players on this roster.</p>
          ) : (
            <PayrollLedger
              players={sandbox.players}
              planSeason={meta.plan_season}
              cbt={current.cbt_threshold}
              highlightIds={sandbox.added}
              onSelect={(id) => openDetail(id)}
            />
          )}
        </section>
      </main>

      {detailId !== null && (
        <DetailPanel
          playerId={detailId}
          planSeason={meta.plan_season}
          statsSeason={meta.stats_season}
          archetypeLabels={archetypeLabels}
          onClose={closeDetail}
          onSelectPlayer={(id) => {
            const p = cache[id];
            setDetailId(id);
            if (p) setArmed(p);
            else void api.player(id).then((full) => setArmed((a) => (a === null || a.id !== full.id ? full : a)));
          }}
          actions={(p) => (
            <PutActions
              key={p.id}
              player={p}
              where={whereLabel(sandbox, p.id)}
              team={roster.team}
              busy={sandbox.busy}
              onPut={(t) => void put(p, t)}
              onRemove={() => {
                setArmed(null);
                void sandbox.toggle(p.id);
              }}
              inTradeOut={trade.out.includes(p.id)}
              inTradeIn={trade.incoming.includes(p.id)}
              onTrade={() => {
                if (p.team === roster.team.abbrev && roster.players.some((r) => r.id === p.id)) {
                  setTrade((t) => ({
                    ...t,
                    out: t.out.includes(p.id) ? t.out.filter((i) => i !== p.id) : [...t.out, p.id],
                  }));
                } else {
                  setTrade((t) => ({
                    ...t,
                    partner: p.team,
                    incoming:
                      t.partner !== p.team
                        ? [p.id]
                        : t.incoming.includes(p.id)
                          ? t.incoming.filter((i) => i !== p.id)
                          : [...t.incoming, p.id],
                  }));
                }
                setTab("trade");
              }}
            />
          )}
        />
      )}
    </>
  );
}

function whereLabel(sandbox: Sandbox, id: number): string | null {
  if (!sandbox.ids.includes(id)) return null;
  const d = sandbox.current.depth;
  for (const [slot, pid] of Object.entries(d.lineup)) if (pid === id) return `starting at ${slot}`;
  if (d.rotation.includes(id)) return "in the rotation";
  if (d.bullpen.includes(id)) return "in the bullpen";
  return "on the bench";
}

function Guide({
  armed,
  busy,
  message,
  onCancel,
}: {
  armed: AnyPlayer | null;
  busy: boolean;
  message: string | null;
  onCancel: () => void;
}) {
  return (
    <div className="flex min-h-14 flex-wrap items-center gap-x-4 gap-y-2 border-y border-line py-2 text-sm">
      {armed ? (
        <>
          <p className="min-w-0 flex-1">
            <span className="font-semibold text-accent-text">{armed.name}</span> is selected.{" "}
            {armed.group === "hitter"
              ? "Click a position on the diamond to put him there."
              : "Put him in the rotation or bullpen beside the diamond."}
          </p>
          <button
            type="button"
            onClick={onCancel}
            className="min-h-10 rounded px-3 font-semibold text-ink-2 hover:bg-surface-2"
          >
            Cancel <span className="text-ink-3">Esc</span>
          </button>
        </>
      ) : (
        <p className="min-w-0 flex-1 text-ink-2" role="status" aria-live="polite">
          {busy
            ? "Updating the depth chart…"
            : (message ?? (
                <>
                  <span className="font-semibold text-ink">Start here:</span> pick a player on the skill map, then click a
                  position on the diamond to put him there.
                </>
              ))}
        </p>
      )}
    </div>
  );
}

function Needs({
  needs,
  cache,
  lineup,
  onFind,
}: {
  needs: TeamRoster["evaluation"]["needs"];
  cache: Record<number, Player>;
  lineup: Record<string, number | null>;
  onFind: (slot: string) => void;
}) {
  if (needs.length === 0)
    return <p className="mt-2 text-sm text-good">No weak spots: every position has an average or better starter.</p>;
  return (
    <section aria-labelledby="needs-heading" className="mt-3">
      <h3 id="needs-heading" className="mb-1 text-xs font-semibold text-ink-3">
        Weak spots <span className="tabular">({needs.length})</span>
      </h3>
      <ul className="divide-y divide-line border-y border-line">
        {needs.map((n) => {
          const id = lineup[n.slot];
          const who = id != null ? cache[id] : undefined;
          return (
            <li key={`${n.slot}-${n.message}`} className="flex min-h-11 items-center gap-3 py-1 text-sm">
              <span className="w-8 shrink-0 font-display font-bold text-bad">{n.slot}</span>
              <span className="min-w-0 flex-1 truncate text-ink-2" title={n.message}>
                {who ? `${who.name} projects below average` : n.message}
              </span>
              <button
                type="button"
                onClick={() => onFind(n.slot)}
                className="min-h-9 shrink-0 rounded border border-line px-2 text-xs font-semibold hover:bg-surface-2"
              >
                Find a replacement
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function Moves({ sandbox, onOpen }: { sandbox: Sandbox; onOpen: (id: number, el?: Element | null) => void }) {
  const row = (id: number, kind: "added" | "removed") => {
    const p = sandbox.cache[id];
    return (
      <li key={`${kind}-${id}`} className="flex min-h-10 items-center gap-2 text-sm">
        <span aria-hidden className={`w-3 font-bold ${kind === "added" ? "text-good" : "text-bad"}`}>
          {kind === "added" ? "+" : "−"}
        </span>
        <button
          type="button"
          onClick={(e) => onOpen(id, e.currentTarget)}
          className="min-w-0 flex-1 truncate text-left hover:underline"
        >
          <span className="sr-only">{kind === "added" ? "Added " : "Removed "}</span>
          {p?.name ?? `Player ${id}`}
          {p && <span className="text-ink-3"> · {p.team} · {positionLabel(p)}</span>}
        </button>
        <button
          type="button"
          disabled={sandbox.busy}
          onClick={() => void sandbox.toggle(id)}
          className="min-h-9 shrink-0 rounded px-2 text-xs font-semibold text-ink-2 hover:bg-surface-2 disabled:cursor-wait"
        >
          {kind === "added" ? "Take off roster" : "Bring back"}
        </button>
      </li>
    );
  };
  return (
    <section aria-labelledby="moves-heading">
      <h3 id="moves-heading" className="mb-1 text-xs font-semibold text-ink-3">
        Your moves vs the actual roster
      </h3>
      <ul className="grid gap-x-6 border-y border-line py-1 sm:grid-cols-2">
        {sandbox.added.map((id) => row(id, "added"))}
        {sandbox.removed.map((id) => row(id, "removed"))}
      </ul>
    </section>
  );
}

function PutActions({
  player,
  where,
  team,
  busy,
  onPut,
  onRemove,
  inTradeOut,
  inTradeIn,
  onTrade,
}: {
  player: Player;
  where: string | null;
  team: Team;
  busy: boolean;
  onPut: (target: string) => void;
  onRemove: () => void;
  inTradeOut: boolean;
  inTradeIn: boolean;
  onTrade: () => void;
}) {
  const [slot, setSlot] = useState(defaultSlot(player));
  const own = player.team === team.abbrev;
  const btn =
    "min-h-10 rounded border border-line px-3 text-sm font-semibold hover:bg-surface-2 disabled:cursor-wait disabled:text-ink-3";
  const primary =
    "min-h-10 rounded bg-accent px-3 text-sm font-semibold text-accent-ink hover:bg-accent/90 disabled:cursor-wait disabled:bg-surface-2 disabled:text-ink-3";
  return (
    <div className="w-full space-y-2">
      <p className="text-xs text-ink-3">{where ? `On your working roster, ${where}.` : "Not on your roster."}</p>
      <div className="flex flex-wrap items-center gap-2">
        {player.group === "hitter" ? (
          <>
            <label className="sr-only" htmlFor="put-slot">
              Position
            </label>
            <select
              id="put-slot"
              value={slot}
              onChange={(e) => setSlot(e.target.value)}
              className="min-h-10 rounded border border-line bg-bg px-2 text-sm font-semibold"
            >
              {LINEUP_ORDER.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button type="button" disabled={busy} onClick={() => onPut(slot)} className={primary}>
              Put at {slot}
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => onPut("rotation")}
              className={player.role === "SP" ? primary : btn}
            >
              Put in rotation
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => onPut("bullpen")}
              className={player.role === "SP" ? btn : primary}
            >
              Put in bullpen
            </button>
          </>
        )}
        {where && (
          <button type="button" disabled={busy} onClick={onRemove} className={btn}>
            Take off roster
          </button>
        )}
        <button type="button" onClick={onTrade} className={btn}>
          {own
            ? inTradeOut
              ? "Remove from trade block"
              : "Add to trade block"
            : inTradeIn
              ? "Remove from trade ask"
              : `Ask ${player.team} for him`}
        </button>
      </div>
    </div>
  );
}
