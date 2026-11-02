import { money, num, signedMoney } from "@/lib/format";
import type { RosterEvaluation } from "@/lib/types";

interface Props {
  current: RosterEvaluation;
  original: RosterEvaluation;
  changed: boolean;
  planSeason: number;
  statsSeason: number;
}

function Delta({ value, kind, goodWhen }: { value: number; kind: "money" | "war"; goodWhen: "up" | "down" }) {
  if (Math.abs(value) < 0.05) return <span className="text-ink-3">No change</span>;
  const good = goodWhen === "up" ? value > 0 : value < 0;
  const text = kind === "money" ? signedMoney(value) : `${value > 0 ? "+" : "−"}${num(Math.abs(value))}`;
  return (
    <span className={good ? "text-good" : "text-bad"}>
      {text} <span className="sr-only">vs actual roster</span>
    </span>
  );
}

/** Headline numbers. Deltas compare the working roster to the team's actual roster. */
export function Scoreboard({ current, original, changed, planSeason, statsSeason }: Props) {
  const over = current.payroll_now > current.cbt_threshold;
  const items = [
    {
      label: `${planSeason} payroll`,
      value: money(current.payroll_now),
      sub: `of ${money(current.cbt_threshold, 0)} tax line`,
      delta: <Delta value={current.payroll_now - original.payroll_now} kind="money" goodWhen="down" />,
      tone: over ? "text-bad" : "",
    },
    {
      label: over ? "Over the tax line" : "Room under tax line",
      value: money(Math.abs(current.cbt_room)),
      sub: "competitive balance tax",
      delta: <Delta value={current.cbt_room - original.cbt_room} kind="money" goodWhen="up" />,
      tone: over ? "text-bad" : "",
    },
    {
      label: `Team sWAR ${statsSeason}`,
      value: num(current.war),
      sub: "StatSlugger WAR",
      delta: <Delta value={current.war - original.war} kind="war" goodWhen="up" />,
      tone: "",
    },
    {
      label: `Projected sWAR ${planSeason}`,
      value: num(current.proj_war),
      sub: "next season",
      delta: <Delta value={current.proj_war - original.proj_war} kind="war" goodWhen="up" />,
      tone: "",
    },
  ];
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
      {items.map((it) => (
        <div key={it.label} className="min-w-0">
          <dt className="truncate text-xs text-ink-3">{it.label}</dt>
          <dd className={`tabular font-display text-3xl font-bold leading-tight ${it.tone}`}>{it.value}</dd>
          <dd className="tabular truncate text-xs">
            {changed ? it.delta : <span className="text-ink-3">{it.sub}</span>}
          </dd>
        </div>
      ))}
    </dl>
  );
}
