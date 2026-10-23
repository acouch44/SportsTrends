/**
 * Build-time readers for ../data (the committed output of the Python pipeline).
 * Server components only: this uses the filesystem.
 */
import fs from "node:fs";
import path from "node:path";
import { ChartBundle, Registry, type RegistryEntry } from "./bundle";

const DATA_DIR = path.resolve(process.cwd(), "..", "data");

function readJson(file: string): unknown {
  if (!fs.existsSync(file)) {
    throw new Error(
      `${file} is missing. Run the pipeline first: st backfill --league nfl && st charts --league nfl`,
    );
  }
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

let registryCache: Registry | null = null;
export function loadRegistry(): Registry {
  if (!registryCache) registryCache = Registry.parse(readJson(path.join(DATA_DIR, "registry.json")));
  return registryCache;
}

const bundleCache = new Map<string, ChartBundle>();
export function loadBundle(league: string, slug: string): ChartBundle {
  const key = `${league}/${slug}`;
  let b = bundleCache.get(key);
  if (!b) {
    b = ChartBundle.parse(readJson(path.join(DATA_DIR, "charts", league, `${slug}.json`)));
    bundleCache.set(key, b);
  }
  return b;
}

export function chartEntries(league?: string): RegistryEntry[] {
  const all = loadRegistry().charts;
  return league ? all.filter((c) => c.league === league) : all;
}

export function leaguesWithCharts(): string[] {
  return Array.from(new Set(loadRegistry().charts.map((c) => c.league)));
}

export function chartParams(): { league: string; slug: string }[] {
  return loadRegistry().charts.map((c) => ({ league: c.league, slug: c.slug }));
}
