"use client";

import type { ChartBundle } from "@/lib/bundle";
import { seriesColor, theme, type Mode } from "@/lib/palette";
import { useMode } from "./hooks";

/** Line-key legend. Present for two or more series; a single series is named by the title. */
export default function Legend({ bundle, mode }: { bundle: ChartBundle; mode?: Mode }) {
  const m = useMode(mode);
  const t = theme(m);
  if (bundle.series.length < 2) return null;
  return (
    <ul className="legend" aria-label="Series">
      {bundle.series.map((s, i) => (
        <li key={s.key}>
          <span className="legend-key" style={{ background: seriesColor(t, s.color, i) }} aria-hidden />
          {s.label}
        </li>
      ))}
    </ul>
  );
}
