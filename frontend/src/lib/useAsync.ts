"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type AsyncState<T> =
  | { status: "loading"; data: T | null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: T | null; error: string };

/** Run an async loader whenever deps change; stale responses are ignored. */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[]): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading", data: null, error: null });
  const [tick, setTick] = useState(0);
  const seq = useRef(0);
  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    const id = ++seq.current;
    setState((s) => ({ status: "loading", data: s.data, error: null }));
    loader().then(
      (data) => id === seq.current && setState({ status: "ready", data, error: null }),
      (err: unknown) =>
        id === seq.current &&
        setState((s) => ({ status: "error", data: s.data, error: err instanceof Error ? err.message : String(err) })),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { ...state, reload };
}
