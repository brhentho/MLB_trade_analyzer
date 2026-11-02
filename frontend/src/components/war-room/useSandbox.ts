"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { LINEUP_ORDER } from "@/lib/format";
import type { AnyPlayer, Player, RosterEvaluation, TeamRoster } from "@/lib/types";

export type Target = string;

export interface Placement {
  playerId: number;
  target: Target;
  /** Where the server's depth chart actually put the player. */
  landed: string | null;
  removedId: number | null;
}

const LINEUP = new Set<string>(LINEUP_ORDER);
export const isLineupSlot = (t: string) => LINEUP.has(t);

export function whereIs(ev: RosterEvaluation, id: number): string | null {
  for (const [slot, pid] of Object.entries(ev.depth.lineup)) if (pid === id) return slot;
  if (ev.depth.rotation.includes(id)) return "rotation";
  if (ev.depth.bullpen.includes(id)) return "bullpen";
  if (ev.depth.bench.includes(id)) return "bench";
  return null;
}

export function targetLabel(t: string | null): string {
  if (t === null) return "off the roster";
  if (t === "rotation") return "the rotation";
  if (t === "bullpen") return "the bullpen";
  if (t === "bench") return "the bench";
  return t;
}

/** Working copy of a team's roster. Remount (key by team) to start over with a new team. */
export function useSandbox(roster: TeamRoster) {
  const originalIds = useMemo(() => roster.players.map((p) => p.id), [roster]);
  const [ids, setIds] = useState<number[]>(originalIds);
  const [evaluation, setEvaluation] = useState<RosterEvaluation | null>(null);
  const [cache, setCache] = useState<Record<number, Player>>(() =>
    Object.fromEntries(roster.players.map((p) => [p.id, p])),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [last, setLast] = useState<Placement | null>(null);
  const seq = useRef(0);

  const current = evaluation ?? roster.evaluation;

  const run = useCallback(async (next: number[], after?: (ev: RosterEvaluation) => void) => {
    const id = ++seq.current;
    setIds(next);
    setBusy(true);
    setError(null);
    try {
      const ev = await api.evaluateRoster(next);
      if (id !== seq.current) return;
      setEvaluation(ev);
      after?.(ev);
    } catch (e) {
      if (id === seq.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (id === seq.current) setBusy(false);
    }
  }, []);

  const ensurePlayer = useCallback(
    async (id: number): Promise<Player> => {
      const hit = cache[id];
      if (hit) return hit;
      const p = await api.player(id);
      setCache((c) => ({ ...c, [id]: p }));
      return p;
    },
    [cache],
  );

  const place = useCallback(
    async (player: AnyPlayer, target: Target) => {
      let full: Player;
      try {
        full = await ensurePlayer(player.id);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return;
      }
      let removed: number | null = null;
      if (isLineupSlot(target)) {
        const occ = current.depth.lineup[target] ?? null;
        if (occ !== null && occ !== full.id) removed = occ;
      } else if (target === "rotation" || target === "bullpen") {
        const list = current.depth[target];
        const replaceAt = target === "rotation" ? 5 : 8;
        if (!list.includes(full.id) && list.length >= replaceAt) {
          const weakest = [...list].sort((a, b) => (cache[a]?.war ?? 0) - (cache[b]?.war ?? 0))[0];
          removed = weakest ?? null;
        }
      }
      const next = ids.filter((i) => i !== removed);
      if (!next.includes(full.id)) next.push(full.id);
      await run(next, (ev) =>
        setLast({ playerId: full.id, target, landed: whereIs(ev, full.id), removedId: removed }),
      );
    },
    [cache, current, ensurePlayer, ids, run],
  );

  const toggle = useCallback(
    async (id: number) => {
      setLast(null);
      if (ids.includes(id)) {
        await run(ids.filter((i) => i !== id));
        return;
      }
      try {
        await ensurePlayer(id);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return;
      }
      await run([...ids, id]);
    },
    [ensurePlayer, ids, run],
  );

  const reset = useCallback(() => {
    seq.current++;
    setIds(originalIds);
    setEvaluation(null);
    setLast(null);
    setError(null);
    setBusy(false);
  }, [originalIds]);

  const retry = useCallback(() => void run(ids), [ids, run]);

  const original = new Set(originalIds);
  const working = new Set(ids);
  const added = ids.filter((i) => !original.has(i));
  const removed = originalIds.filter((i) => !working.has(i));
  const players = ids.map((i) => cache[i]).filter((p): p is Player => p !== undefined);

  return {
    ids,
    cache,
    players,
    current,
    original: roster.evaluation,
    changed: added.length > 0 || removed.length > 0,
    added,
    removed,
    busy,
    error,
    last,
    place,
    toggle,
    reset,
    retry,
  };
}

export type Sandbox = ReturnType<typeof useSandbox>;
