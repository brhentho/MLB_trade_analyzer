"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { filtersToChips, removeChip } from "@/lib/chips";
import type { NaturalSearchResult, SearchFilters, SearchResult } from "@/lib/types";

export interface ScoutSearchState {
  query: string;
  filters: SearchFilters | null;
  result: SearchResult | null;
  notes: string[];
  interpretedBy: "ai" | "rules" | null;
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;
}

/** Natural-language scout search where the interpretation is shown as editable chips. */
export function useScoutSearch(limit = 25) {
  const [state, setState] = useState<ScoutSearchState>({
    query: "",
    filters: null,
    result: null,
    notes: [],
    interpretedBy: null,
    status: "idle",
    error: null,
  });

  const runQuery = async (query: string) => {
    if (query.trim().length < 2) return;
    setState((s) => ({ ...s, query, status: "loading", error: null }));
    try {
      const r: NaturalSearchResult = await api.naturalSearch(query, limit);
      setState({
        query,
        filters: r.filters,
        result: r,
        notes: r.notes,
        interpretedBy: r.interpreted_by,
        status: "ready",
        error: null,
      });
    } catch (e) {
      setState((s) => ({ ...s, status: "error", error: e instanceof Error ? e.message : String(e) }));
    }
  };

  const runFilters = async (filters: SearchFilters) => {
    setState((s) => ({ ...s, filters, status: "loading", error: null }));
    try {
      const r = await api.search({ ...filters, limit });
      setState((s) => ({ ...s, filters, result: r, status: "ready" }));
    } catch (e) {
      setState((s) => ({ ...s, status: "error", error: e instanceof Error ? e.message : String(e) }));
    }
  };

  const dropChip = (chipId: string) => state.filters && runFilters(removeChip(state.filters, chipId));

  return { state, runQuery, runFilters, dropChip };
}

interface BoxProps {
  onSubmit: (q: string) => void;
  busy: boolean;
  examples?: string[];
  placeholder?: string;
  label?: string;
}

export function ScoutQueryBox({
  onSubmit,
  busy,
  examples = [],
  placeholder = "Left-handed reliever, elite chase rate, under $6M, 2+ years of control",
  label = "Describe the player you need",
}: BoxProps) {
  const [q, setQ] = useState("");
  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(q);
        }}
        className="flex gap-2"
        role="search"
      >
        <label htmlFor="scout-query" className="sr-only">
          {label}
        </label>
        <input
          id="scout-query"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={placeholder}
          className="min-h-10 flex-1 rounded border border-line bg-surface px-3 text-sm text-ink placeholder:text-ink-3"
        />
        <button
          type="submit"
          disabled={busy || q.trim().length < 2}
          className="min-h-10 rounded bg-accent px-4 text-sm font-semibold text-accent-ink transition-opacity duration-fast ease-out disabled:opacity-50"
        >
          {busy ? "Searching…" : "Find players"}
        </button>
      </form>
      {examples.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-3">
          <span>Try</span>
          {examples.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setQ(ex);
                onSubmit(ex);
              }}
              className="min-h-8 rounded border border-line px-2 text-ink-2 hover:border-ink-3 hover:text-ink"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function FilterChips({
  filters,
  archetypeLabels,
  onRemove,
  interpretedBy,
  notes,
}: {
  filters: SearchFilters;
  archetypeLabels?: Record<string, string>;
  onRemove: (id: string) => void;
  interpretedBy?: "ai" | "rules" | null;
  notes?: string[];
}) {
  const chips = filtersToChips(filters, archetypeLabels);
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="text-ink-3">{interpretedBy === "ai" ? "Read by AI as" : "Read as"}</span>
      {chips.length === 0 && <span className="text-ink-2">no constraints</span>}
      {chips.map((c) => (
        <button
          key={c.id}
          type="button"
          onClick={() => onRemove(c.id)}
          aria-label={`Remove ${c.label}`}
          className="group inline-flex min-h-7 items-center gap-1 rounded-full border border-line bg-surface-2 px-2.5 font-medium text-ink hover:border-bad"
        >
          {c.label}
          <span aria-hidden className="text-ink-3 group-hover:text-bad">
            ×
          </span>
        </button>
      ))}
      {notes?.map((n) => (
        <span key={n} className="text-ink-3">
          · {n}
        </span>
      ))}
    </div>
  );
}
