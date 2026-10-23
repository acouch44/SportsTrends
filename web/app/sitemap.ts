import type { MetadataRoute } from "next";
import { leaguesWithCharts, loadRegistry } from "@/lib/registry";
import { SITE_URL, chartUrl } from "@/lib/site";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const reg = loadRegistry();
  return [
    { url: `${SITE_URL}/`, lastModified: reg.generated_at, changeFrequency: "daily", priority: 1 },
    ...leaguesWithCharts().map((l) => ({
      url: `${SITE_URL}/${l}/`,
      lastModified: reg.generated_at,
      changeFrequency: "daily" as const,
      priority: 0.8,
    })),
    ...reg.charts.map((c) => ({
      url: chartUrl(c.league, c.slug),
      lastModified: c.generated_at,
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
  ];
}
