import Image from "next/image";
import Link from "next/link";

const TREATMENTS = [
  {
    href: "/lab/front-office",
    name: "Front office terminal",
    pitch: "Dense, sortable, keyboard-first grids. Closest to Out of the Park Baseball.",
    tradeoff: "Fastest for scanning hundreds of players; least approachable.",
  },
  {
    href: "/lab/scouting-report",
    name: "Scouting report",
    pitch: "Players as cards with a 20–80 scouting sheet on the back. Build a binder; swap cards to trade.",
    tradeoff: "Most approachable and shareable; slower to compare many players.",
  },
  {
    href: "/lab/war-room",
    name: "Diamond war room",
    pitch: "The roster lives on a diamond. Find players on a skill map, then drop them into a position.",
    tradeoff: "Most novel; spatial views take longer to learn.",
  },
];

const SCENARIOS = [
  ["Take over a team", "What do I have, what do I owe, and where are the holes?"],
  ["Find a niche player", "“Lefty reliever, elite chase rate, under $6M, 2+ years of control.”"],
  ["Find a cheaper comp", "Who plays like this player but costs less or is younger?"],
  ["Build the perfect team", "Pick real players under a budget and see the depth chart fill in."],
  ["Grade a trade", "Surplus value, payroll impact and years of control, with a plain-language read."],
];

export default function Home() {
  return (
    <main data-theme="paper" className="min-h-screen bg-bg text-ink">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <header className="flex items-center gap-4">
          <Image src="/brand/logo.png" alt="" width={72} height={72} className="rounded" priority />
          <div>
            <h1 className="font-display text-4xl font-bold tracking-tight">StatSlugger</h1>
            <p className="text-ink-2">Run a real front office: real MLB players, real stats, real contracts.</p>
          </div>
        </header>

        <section className="mt-10" aria-labelledby="treatments">
          <h2 id="treatments" className="text-sm font-semibold text-ink-3">
            Three treatments, same data
          </h2>
          <ul className="mt-3 grid gap-4 md:grid-cols-3">
            {TREATMENTS.map((t) => (
              <li key={t.href}>
                <Link
                  href={t.href}
                  className="block h-full rounded-lg border border-line bg-surface p-5 transition-colors duration-fast ease-out hover:border-accent"
                >
                  <span className="font-display text-2xl font-bold">{t.name}</span>
                  <p className="mt-2 text-sm">{t.pitch}</p>
                  <p className="mt-3 text-xs text-ink-3">{t.tradeoff}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-10" aria-labelledby="scenarios">
          <h2 id="scenarios" className="text-sm font-semibold text-ink-3">
            What each one has to do
          </h2>
          <dl className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2">
            {SCENARIOS.map(([k, v]) => (
              <div key={k}>
                <dt className="font-semibold">{k}</dt>
                <dd className="text-sm text-ink-2">{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <p className="mt-12 text-xs text-ink-3">
          Stats from the MLB Stats API and Baseball Savant. Ratings, sWAR and surplus value are StatSlugger estimates.
          Contracts marked “estimate” are derived from service time, not reported figures.
        </p>
      </div>
    </main>
  );
}
