import Link from "next/link";
import type { ChartBundle } from "@/lib/bundle";
import { longDate } from "@/lib/format";
import { LEAGUES } from "@/lib/site";
import Chart from "./charts/Chart";

/** A gallery entry: a live, axis-free preview of the real chart above its title and hook. */
export default function ChartTile({ bundle, featured = false }: { bundle: ChartBundle; featured?: boolean }) {
  const league = (LEAGUES as Record<string, string>)[bundle.league] ?? bundle.league.toUpperCase();
  const height = featured ? 260 : 170;
  return (
    <Link href={`/${bundle.league}/${bundle.slug}/`} className={`tile${featured ? " tile-featured" : ""}`}>
      <div className="tile-chart">
        <Chart bundle={bundle} variant="compact" height={height} />
      </div>
      <h2 className="display tile-title">{bundle.title}</h2>
      <p className="tile-hook">{bundle.hook}</p>
      <p className="tile-meta">
        <span className="league-tag">{league}</span>
        <span>Through {longDate(bundle.data_through)}</span>
      </p>
    </Link>
  );
}
