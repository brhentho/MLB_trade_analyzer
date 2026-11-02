import type {
  Archetype,
  Group,
  Meta,
  NaturalSearchResult,
  Player,
  PlayerSummary,
  Ratings,
  RosterEvaluation,
  SearchFilters,
  SearchResult,
  ShapeResult,
  SimilarResult,
  Team,
  TeamRoster,
  TradeEvaluation,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(`Can't reach the StatSlugger API at ${API_URL}. Start it with "python backend/main.py".`, 0);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail))
        detail = body.detail
          .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg ?? "invalid"}`)
          .join("; ");
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  meta: () => request<Meta>("/api/meta"),
  teams: () => request<Team[]>("/api/teams"),
  roster: (team: string) => request<TeamRoster>(`/api/teams/${encodeURIComponent(team)}/roster`),
  players: (opts: { group?: Group; team?: string; mapped?: boolean } = {}) => {
    const q = new URLSearchParams();
    if (opts.group) q.set("group", opts.group);
    if (opts.team) q.set("team", opts.team);
    if (opts.mapped) q.set("mapped", "true");
    return request<PlayerSummary[]>(`/api/players?${q.toString()}`);
  },
  player: (id: number) => request<Player>(`/api/players/${id}`),
  similar: (id: number, opts: { limit?: number; salary_max?: number; control_min_years?: number } = {}) => {
    const q = new URLSearchParams();
    Object.entries(opts).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return request<SimilarResult>(`/api/players/${id}/similar?${q.toString()}`);
  },
  search: (filters: SearchFilters) => post<SearchResult>("/api/players/search", filters),
  naturalSearch: (query: string, limit = 25) =>
    post<NaturalSearchResult>("/api/players/search/natural", { query, limit }),
  shape: (group: Group, profile: Ratings, limit = 12) => post<ShapeResult>("/api/players/shape", { group, profile, limit }),
  archetypes: () => request<Archetype[]>("/api/archetypes"),
  evaluateRoster: (player_ids: number[], budget?: number) =>
    post<RosterEvaluation>("/api/rosters/evaluate", { player_ids, budget }),
  evaluateTrade: (body: {
    team_a: string;
    team_b: string;
    team_a_receives: number[];
    team_b_receives: number[];
    context?: string;
    use_ai?: boolean;
  }) => post<TradeEvaluation>("/api/trades/evaluate", body),
};
