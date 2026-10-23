import type { Metadata } from "next";
import ChartTile from "@/components/ChartTile";
import { chartEntries, leaguesWithCharts, loadBundle } from "@/lib/registry";
import { LEAGUES } from "@/lib/site";

export const dynamicParams = false;

export function generateStaticParams() {
  return leaguesWithCharts().map((league) => ({ league }));
}

export async function generateMetadata({ params }: { params: Promise<{ league: string }> }): Promise<Metadata> {
  const { league } = await params;
  const name = (LEAGUES as Record<string, string>)[league] ?? league.toUpperCase();
  return { title: `${name} charts`, description: `How the ${name} has changed, in charts you can share.` };
}

export default async function LeaguePage({ params }: { params: Promise<{ league: string }> }) {
  const { league } = await params;
  const name = (LEAGUES as Record<string, string>)[league] ?? league.toUpperCase();
  const bundles = chartEntries(league).map((e) => loadBundle(e.league, e.slug));
  return (
    <>
      <section className="mb-10">
        <h1 className="display" style={{ fontSize: "clamp(2.4rem, 6vw, 4rem)", margin: 0 }}>
          {name}
        </h1>
        <p className="lead mt-3">
          {bundles.length} chart{bundles.length === 1 ? "" : "s"}, from decade-long trends to the wildest game of
          the week.
        </p>
      </section>
      <section className="tiles" aria-label={`${name} charts`}>
        {bundles.map((b) => (
          <ChartTile key={b.id} bundle={b} />
        ))}
      </section>
    </>
  );
}
