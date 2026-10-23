export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "https://sportstrends.vercel.app").replace(/\/$/, "");
export const SITE_NAME = "SportsTrends";
export const SITE_TAGLINE = "Sports history, one chart at a time.";
export const SITE_DESCRIPTION =
  "Shareable charts of how the NFL, NBA, NHL and MLB have changed: decade-long trends down to the wildest game of the week.";

export const LEAGUES = { nfl: "NFL", nba: "NBA", nhl: "NHL", mlb: "MLB" } as const;
export type League = keyof typeof LEAGUES;

export const FORMATS = {
  og: { w: 1200, h: 630, label: "Link preview" },
  square: { w: 1080, h: 1080, label: "Square" },
  portrait: { w: 1080, h: 1350, label: "Portrait" },
  story: { w: 1080, h: 1920, label: "Story" },
} as const;
export type Format = keyof typeof FORMATS;
export const FORMAT_KEYS = Object.keys(FORMATS) as Format[];

export function chartUrl(league: string, slug: string): string {
  return `${SITE_URL}/${league}/${slug}/`;
}

export function ogImageUrl(league: string, slug: string, version: string): string {
  return `${SITE_URL}/og/${league}/${slug}.png?v=${encodeURIComponent(version)}`;
}

export function hostLabel(): string {
  return SITE_URL.replace(/^https?:\/\//, "");
}
