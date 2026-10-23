import ChartTile from "@/components/ChartTile";
import { chartEntries, loadBundle } from "@/lib/registry";
import { SITE_DESCRIPTION, SITE_TAGLINE } from "@/lib/site";

export default function Home() {
  const entries = chartEntries();
  const bundles = entries.map((e) => loadBundle(e.league, e.slug));
  const featuredIdx = Math.max(
    0,
    bundles.findIndex((b) => b.kind === "wp_story"),
  );
  const featured = bundles[featuredIdx];
  const rest = bundles.filter((_, i) => i !== featuredIdx);
  return (
    <>
      <section className="mb-12">
        <h1 className="display" style={{ fontSize: "clamp(2.6rem, 7vw, 5rem)", margin: 0 }}>
          {SITE_TAGLINE}
        </h1>
        <p className="lead mt-4">{SITE_DESCRIPTION}</p>
      </section>
      <section className="tiles" aria-label="Charts">
        {featured && <ChartTile bundle={featured} featured />}
        {rest.map((b) => (
          <ChartTile key={b.id} bundle={b} />
        ))}
      </section>
    </>
  );
}
