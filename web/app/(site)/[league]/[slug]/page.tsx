import type { Metadata } from "next";
import Link from "next/link";
import CaptionPanel from "@/components/CaptionPanel";
import ChartTile from "@/components/ChartTile";
import DataTable from "@/components/DataTable";
import ShareBar from "@/components/ShareBar";
import Chart from "@/components/charts/Chart";
import Legend from "@/components/charts/Legend";
import type { Story } from "@/lib/bundle";
import { fmt, fmtElapsed, longDate } from "@/lib/format";
import { chartEntries, chartParams, loadBundle } from "@/lib/registry";
import { LEAGUES, SITE_NAME, chartUrl, ogImageUrl } from "@/lib/site";
import { pageHeight } from "@/lib/sizes";

export const dynamicParams = false;

export function generateStaticParams() {
  return chartParams();
}

type Params = Promise<{ league: string; slug: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { league, slug } = await params;
  const b = loadBundle(league, slug);
  const url = chartUrl(league, slug);
  const image = ogImageUrl(league, slug, b.data_through || b.generated_at);
  const description = b.social.alt_text || b.hook || b.subtitle;
  return {
    title: b.title,
    description,
    alternates: { canonical: `/${league}/${slug}/` },
    openGraph: {
      title: b.title,
      description,
      url,
      siteName: SITE_NAME,
      type: "article",
      images: [{ url: image, width: 1200, height: 630, alt: b.social.alt_text || b.title }],
    },
    twitter: { card: "summary_large_image", title: b.title, description, images: [image] },
  };
}

function KeyPlays({ story }: { story: Story }) {
  const pct = fmt(".0%");
  if (!story.key_plays.length) return null;
  return (
    <ol className="plays" aria-label="Biggest swings">
      {story.key_plays.map((k, i) => (
        <li key={k.elapsed}>
          <span className="play-n" aria-hidden>
            {i + 1}
          </span>
          <div>
            <div className="play-meta">
              {fmtElapsed(k.elapsed)}, {story.home} {pct(k.wp_before)} to {pct(k.wp_after)}. Score after: {k.score}
            </div>
            <div>{k.desc}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default async function ChartPage({ params }: { params: Params }) {
  const { league, slug } = await params;
  const b = loadBundle(league, slug);
  const url = chartUrl(league, slug);
  const leagueName = (LEAGUES as Record<string, string>)[league] ?? league.toUpperCase();
  const more = chartEntries()
    .filter((c) => c.id !== b.id)
    .slice(0, 3)
    .map((c) => loadBundle(c.league, c.slug));

  return (
    <article>
      <p className="m-0">
        <Link href={`/${league}/`} className="league-tag no-underline">
          {leagueName}
        </Link>
      </p>
      <h1 className="display mt-2 mb-3" style={{ fontSize: "clamp(2.2rem, 5.5vw, 3.6rem)" }}>
        {b.title}
      </h1>
      {b.subtitle && <p className="lead m-0">{b.subtitle}</p>}
      {b.hook && <p className="hook mt-4 mb-6">{b.hook}</p>}

      <section className="panel" aria-label="Chart">
        <Legend bundle={b} />
        <Chart bundle={b} variant="full" height={pageHeight(b.kind)} />
      </section>
      {b.story && <KeyPlays story={b.story} />}

      <ShareBar bundle={b} url={url} />
      <CaptionPanel social={b.social} url={url} />
      <DataTable bundle={b} />

      <p className="mt-8 text-sm" style={{ color: "var(--ink2)" }}>
        Source: <a href={b.source.url}>{b.source.name}</a>
        {b.source.license ? ` (${b.source.license})` : ""}. Data through {longDate(b.data_through)}; chart built{" "}
        {longDate(b.generated_at.slice(0, 10))}.
      </p>

      {more.length > 0 && (
        <section className="mt-16" aria-labelledby="more-h">
          <h2 id="more-h" className="display mb-6" style={{ fontSize: "1.9rem" }}>
            More charts
          </h2>
          <div className="tiles">
            {more.map((m) => (
              <ChartTile key={m.id} bundle={m} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
