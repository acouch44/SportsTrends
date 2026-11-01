import Link from "next/link";
import { leaguesWithCharts } from "@/lib/registry";
import { LEAGUES, SITE_NAME } from "@/lib/site";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  const leagues = leaguesWithCharts();
  return (
    <>
      <header className="site-head">
        <div className="wrap">
          <Link href="/" className="wordmark">
            {SITE_NAME}
          </Link>
          <nav className="site-nav" aria-label="Leagues">
            {leagues.map((l) => (
              <Link key={l} href={`/${l}/`}>
                {(LEAGUES as Record<string, string>)[l] ?? l.toUpperCase()}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="wrap flex-1 w-full pt-10">{children}</main>
      <footer className="site-foot">
        <div className="wrap">
          <span>
            Every chart is built from public play-by-play data and names its source. Numbers refresh nightly in
            season.
          </span>
        </div>
      </footer>
    </>
  );
}
