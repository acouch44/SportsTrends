import { format as d3format } from "d3";

export type Fmt = (v: number) => string;

/** Seconds since kickoff -> "Q2 07:30" (regulation 15-minute quarters, 10-minute overtime). */
export function fmtElapsed(s: number): string {
  if (s < 3600) {
    const q = Math.floor(s / 900) + 1;
    const rem = 900 - (s % 900);
    return `Q${q} ${clock(rem)}`;
  }
  const ot = Math.floor((s - 3600) / 600) + 1;
  const rem = 600 - ((s - 3600) % 600);
  return `${ot > 1 ? `OT${ot}` : "OT"} ${clock(rem)}`;
}

function clock(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Quarter boundaries and labels for a win-probability x axis. */
export function quarterMarks(maxElapsed: number): { starts: number[]; labels: string[] } {
  const starts = [0, 900, 1800, 2700];
  const labels = ["Q1", "Q2", "Q3", "Q4"];
  let t = 3600;
  let n = 1;
  while (maxElapsed > t) {
    starts.push(t);
    labels.push(n === 1 ? "OT" : `OT${n}`);
    t += 600;
    n += 1;
  }
  return { starts, labels };
}

const cache = new Map<string, Fmt>();

/** A d3-format spec from the bundle, plus the site's own "elapsed" and "d" conveniences. */
export function fmt(spec: string | null | undefined): Fmt {
  if (!spec) return (v) => String(v);
  const hit = cache.get(spec);
  if (hit) return hit;
  let f: Fmt;
  if (spec === "elapsed") f = fmtElapsed;
  else if (spec === "d") f = (v) => String(Math.round(v));
  else {
    try {
      const g = d3format(spec);
      f = (v) => g(v);
    } catch {
      f = (v) => String(v);
    }
  }
  cache.set(spec, f);
  return f;
}

/** 12,345 -> "12.3K" style compact numbers for axis ticks and bar values. */
export const compact: Fmt = (v) => {
  const a = Math.abs(v);
  if (a >= 1e6) return `${(v / 1e6).toFixed(1).replace(/\.0$/, "")}M`;
  if (a >= 1e4) return `${(v / 1e3).toFixed(0)}K`;
  if (a >= 1e3) return `${(v / 1e3).toFixed(1).replace(/\.0$/, "")}K`;
  return String(Math.round(v));
};

export function longDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}
