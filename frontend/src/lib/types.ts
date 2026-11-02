export type Group = "hitter" | "pitcher";
export type HitterRatingKey = "contact" | "power" | "eye" | "speed" | "glove" | "arm";
export type PitcherRatingKey = "stuff" | "contact_mgmt" | "control" | "velocity" | "stamina";
export type RatingKey = HitterRatingKey | PitcherRatingKey;
export type Ratings = Partial<Record<RatingKey, number | null>>;

export type ContractStatus = "guaranteed" | "pre-arb" | "arbitration" | "estimated";

export interface ContractYear {
  year: number;
  salary: number;
}

export interface ContractSummary {
  status: ContractStatus;
  salary_now: number;
  aav: number;
  control_through: number;
  verified: boolean;
}

export interface Contract extends ContractSummary {
  years: ContractYear[];
  signed: string | null;
  notes: string;
  source: string | null;
  as_of: string | null;
}

export interface PlayerSummary {
  id: number;
  name: string;
  team: string;
  team_id: number;
  group: Group;
  position: string;
  role: string;
  bats: string | null;
  throws: string | null;
  age: number;
  ratings: Ratings;
  ovr: number;
  pot: number;
  war: number;
  proj_war: number | null;
  surplus: number;
  archetypes: string[];
  map: { x: number; y: number } | null;
  contract: ContractSummary;
}

export interface HitterStats {
  g: number;
  pa: number;
  hr: number;
  r: number;
  rbi: number;
  sb: number;
  avg: number | null;
  obp: number | null;
  slg: number | null;
  ops: number | null;
  woba: number | null;
  xwoba: number | null;
  k_pct: number | null;
  bb_pct: number | null;
}

export interface PitcherStats {
  g: number;
  gs: number;
  ip: number;
  era: number | null;
  fip: number | null;
  whip: number | null;
  so: number;
  bb: number;
  k_pct: number | null;
  bb_pct: number | null;
  sv: number;
  hld: number;
  w: number;
  l: number;
}

export interface Player extends Omit<PlayerSummary, "contract" | "proj_war"> {
  two_way: boolean;
  debut: string | null;
  status: string | null;
  percentiles: Record<string, number>;
  stats: Partial<HitterStats & PitcherStats>;
  proj_war: number[];
  contract: Contract;
}

export type AnyPlayer = Player | PlayerSummary;

export interface Team {
  id: number;
  name: string;
  abbrev: string;
  short: string;
  league: string;
  division: string;
  payroll: Record<string, number>;
  payroll_now: number;
  war: number;
}

export interface Need {
  slot: string;
  severity: "empty" | "weak";
  message: string;
}

export interface RosterEvaluation {
  count: number;
  /** Players counted in war/proj_war: the best 26 by depth chart. */
  active_count: number;
  payroll: Record<string, number>;
  payroll_now: number;
  cbt_threshold: number;
  cbt_room: number;
  budget: number | null;
  budget_room: number | null;
  war: number;
  proj_war: number;
  surplus: number;
  depth: {
    lineup: Record<string, number | null>;
    bench: number[];
    rotation: number[];
    bullpen: number[];
  };
  needs: Need[];
  expiring: number[];
}

export interface TeamRoster {
  team: Team;
  players: Player[];
  evaluation: RosterEvaluation;
}

export interface Reason {
  label: string;
  kind: "position" | "bio" | "archetype" | "rating" | "percentile" | "money" | "value";
  value?: number;
}

export interface SearchFilters {
  group?: Group;
  positions?: string[];
  roles?: ("SP" | "RP")[];
  bats?: string[];
  throws?: string[];
  teams?: string[];
  age_min?: number;
  age_max?: number;
  archetypes?: string[];
  ratings_min?: Partial<Record<RatingKey, number>>;
  ratings_max?: Partial<Record<RatingKey, number>>;
  percentiles_min?: Record<string, number>;
  salary_max?: number;
  control_min_years?: number;
  war_min?: number;
  verified_only?: boolean;
  sort?: string;
  descending?: boolean;
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  total: number;
  filters: SearchFilters;
  results: { player: Player; reasons: Reason[] }[];
}

export interface NaturalSearchResult extends SearchResult {
  query: string;
  interpreted_by: "ai" | "rules";
  notes: string[];
}

export interface SimilarResult {
  target: Player;
  results: {
    player: Player;
    similarity: number;
    salary_delta: number;
    control_delta: number;
    age_delta: number;
  }[];
}

export interface ShapeResult {
  profile: Ratings;
  results: { player: Player; similarity: number }[];
}

export interface Archetype {
  id: string;
  label: string;
  group: Group;
  description: string;
  profile: Ratings;
  count: number;
}

export interface TradeSide {
  players: number[];
  surplus: number;
  war: number;
  proj_war_next: number;
  salary_now: number;
  payroll: Record<string, number>;
  control_years: number;
  unverified_contracts: number[];
}

export interface TradeEvaluation {
  grade: string;
  fairness_score: number;
  winner: "team_a" | "team_b" | "even";
  surplus_diff: number;
  team_a: TradeSide;
  team_b: TradeSide;
  payroll_delta_team_a: Record<string, number>;
  summary: string;
  team_a_analysis: string;
  team_b_analysis: string;
  risks: string[];
  recommendation: string;
  narrative_source: "ai" | "rules";
  team_a_name: string;
  team_b_name: string;
  team_a_players: PlayerSummary[];
  team_b_players: PlayerSummary[];
}

export interface Meta {
  stats_season: number;
  plan_season: number;
  generated_at: string;
  ai_available: boolean;
  league: { woba: number; era: number; fip_constant: number };
  assumptions: {
    dollars_per_war_m: number;
    league_min_m: number;
    cbt_threshold_m: number;
    war: string;
  };
  sources: string[];
  ratings: { hitter: HitterRatingKey[]; pitcher: PitcherRatingKey[]; labels: Record<RatingKey, string> };
  percentile_labels: Record<string, string>;
}
