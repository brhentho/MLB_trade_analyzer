import { STATUS_LABEL, money } from "@/lib/format";
import type { AnyPlayer, ContractYear } from "@/lib/types";

interface Props {
  player: AnyPlayer;
  planSeason: number;
  /** Show at most this many seasons; overflow is summarised as +N. */
  max?: number;
}

/**
 * Years of control as pips: filled = guaranteed money, outlined = pre-arb/arb/estimated.
 */
export function ControlPips({ player, planSeason, max = 8 }: Props) {
  const end = player.contract.control_through;
  const years = Math.max(0, end - planSeason + 1);
  const shown = Math.min(years, max);
  const guaranteed = player.contract.status === "guaranteed";
  const salaries: ContractYear[] | undefined = "years" in player.contract ? player.contract.years : undefined;
  const label = years
    ? `${years} season${years === 1 ? "" : "s"} of control through ${end} (${STATUS_LABEL[player.contract.status]})`
    : "No control beyond this season";
  return (
    <span className="inline-flex items-center gap-1" role="img" aria-label={label} title={label}>
      {Array.from({ length: shown }, (_, i) => {
        const y = planSeason + i;
        const sal = salaries?.find((s) => s.year === y)?.salary;
        return (
          <span
            key={y}
            title={sal !== undefined ? `${y}: ${money(sal)}` : String(y)}
            className={`h-2 w-2 rounded-full ${guaranteed ? "bg-accent" : "border border-accent bg-transparent"}`}
          />
        );
      })}
      {years > max && <span className="tabular text-[10px] text-ink-3">+{years - max}</span>}
      {years === 0 && <span className="text-xs text-ink-3">FA</span>}
    </span>
  );
}
