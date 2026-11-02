"use client";

import { useMemo } from "react";
import { api } from "./api";
import type { Archetype, Meta, Team } from "./types";
import { useAsync } from "./useAsync";

export interface LabData {
  meta: Meta;
  teams: Team[];
  archetypes: Archetype[];
  archetypeLabels: Record<string, string>;
}

/** Meta, teams and archetypes: the reference data every treatment needs. */
export function useLabData() {
  const state = useAsync(async () => {
    const [meta, teams, archetypes] = await Promise.all([api.meta(), api.teams(), api.archetypes()]);
    return { meta, teams, archetypes };
  }, []);
  const data: LabData | null = useMemo(() => {
    if (!state.data) return null;
    return {
      ...state.data,
      archetypeLabels: Object.fromEntries(state.data.archetypes.map((a) => [a.id, a.label])),
    };
  }, [state.data]);
  return { ...state, data };
}
