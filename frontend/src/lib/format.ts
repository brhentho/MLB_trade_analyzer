import type { AnyPlayer, Group, RatingKey } from "./types";

export const HITTER_KEYS: RatingKey[] = ["contact", "power", "eye", "speed", "glove", "arm"];
export const PITCHER_KEYS: RatingKey[] = ["stuff", "contact_mgmt", "control", "velocity", "stamina"];

export const RATING_LABELS: Record<RatingKey, string> = {
  contact: "Contact",
  power: "Power",
  eye: "Eye",
  speed: "Speed",
  glove: "Glove",
  arm: "Arm",
  stuff: "Stuff",
  contact_mgmt: "Weak contact",
  control: "Control",
  velocity: "Velocity",
  stamina: "Stamina",
};

export const RATING_SHORT: Record<RatingKey, string> = {
  contact: "CON",
  power: "POW",
  eye: "EYE",
  speed: "SPD",
  glove: "GLV",
  arm: "ARM",
  stuff: "STF",
  contact_mgmt: "WKC",
  control: "CTL",
  velocity: "VEL",
  stamina: "STA",
};

export const ratingKeys = (group: Group) => (group === "hitter" ? HITTER_KEYS : PITCHER_KEYS);

/** Money is stored in millions. */
export function money(m: number | null | undefined, digits = 1): string {
  if (m === null || m === undefined || Number.isNaN(m)) return "—";
  const sign = m < 0 ? "−" : "";
  const abs = Math.abs(m);
  if (abs >= 1000) return `${sign}$${(abs / 1000).toFixed(2)}B`;
  if (abs < 1) return `${sign}$${Math.round(abs * 1000)}K`;
  return `${sign}$${abs.toFixed(digits)}M`;
}

export function signedMoney(m: number, digits = 1): string {
  return m > 0 ? `+${money(m, digits)}` : money(m, digits);
}

export function rate(v: number | null | undefined, digits = 3): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(digits).replace(/^0(?=\.)/, "");
}

export function num(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(digits);
}

/** OOTP-style display: round to the nearest 5 on the 20-80 scale. */
export function scout5(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return String(Math.round(v / 5) * 5);
}

/** 0..1 position of a 20-80 rating, used to mix the rating color tokens. */
export function ratingT(v: number | null | undefined): number {
  if (v === null || v === undefined) return 0;
  return Math.min(1, Math.max(0, (v - 30) / 45));
}

export function ratingColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "rgb(var(--line))";
  const pct = Math.round(ratingT(v) * 100);
  return `color-mix(in oklab, rgb(var(--rating-hi)) ${pct}%, rgb(var(--rating-lo)))`;
}

export function ratingWord(v: number | null | undefined): string {
  if (v === null || v === undefined) return "No data";
  if (v >= 70) return "Plus-plus";
  if (v >= 60) return "Plus";
  if (v >= 55) return "Above average";
  if (v >= 45) return "Average";
  if (v >= 40) return "Below average";
  return "Well below";
}

export function controlYears(p: AnyPlayer, planSeason: number): number {
  return Math.max(0, p.contract.control_through - planSeason + 1);
}

export const STATUS_LABEL: Record<string, string> = {
  guaranteed: "Signed",
  "pre-arb": "Pre-arb",
  arbitration: "Arb",
  estimated: "Est.",
};

export function positionLabel(p: AnyPlayer): string {
  return p.group === "pitcher" ? p.role : p.position;
}

export function handedness(p: AnyPlayer): string {
  return p.group === "pitcher" ? `Throws ${p.throws ?? "?"}` : `Bats ${p.bats ?? "?"}`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
}

export const LINEUP_ORDER = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"] as const;
