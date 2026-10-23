"use client";

import * as Plot from "@observablehq/plot";
import { useEffect, useRef } from "react";
import { col } from "@/lib/bundle";
import { fmt, fmtElapsed, quarterMarks } from "@/lib/format";
import { theme } from "@/lib/palette";
import { useMode, useSize } from "./hooks";
import type { ChartProps } from "./types";

interface Pt {
  t: number;
  wp: number;
}

/** One game's home win probability over game time, with the three biggest swings numbered. */
export default function WpStory(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const box = useRef<HTMLDivElement>(null);
  const mode = useMode(props.mode);
  const { width, height } = useSize(box, { width: props.width, height: props.height ?? 400 });

  useEffect(() => {
    const el = box.current;
    const story = bundle.story;
    if (!el || !width || !height || !bundle.data || !story) return;
    const t = theme(mode);
    const table = bundle.data;
    const ti = col(table, "elapsed");
    const wi = col(table, "wp");
    const rows: Pt[] = table.rows.map((r) => ({ t: Number(r[ti]), wp: Number(r[wi]) }));
    const maxT = Math.max(3600, ...rows.map((r) => r.t));
    const { starts, labels } = quarterMarks(maxT);
    const pct = fmt(".0%");
    const compact = variant === "compact";
    const hover = variant === "full";
    const plays = story.key_plays.map((k, n) => ({ ...k, n: n + 1 }));

    const marks: Plot.Markish[] = [
      Plot.areaY(rows, {
        x: "t",
        y1: 0.5,
        y2: (d: Pt) => Math.max(d.wp, 0.5),
        fill: story.home_color,
        fillOpacity: 0.14,
      }),
      Plot.areaY(rows, {
        x: "t",
        y1: (d: Pt) => Math.min(d.wp, 0.5),
        y2: 0.5,
        fill: story.away_color,
        fillOpacity: 0.14,
      }),
    ];
    if (!compact) {
      marks.push(Plot.gridY({ stroke: t.grid, strokeOpacity: 1, ticks: [0.25, 0.75] }));
      marks.push(Plot.ruleX(starts.slice(1), { stroke: t.grid }));
    }
    marks.push(Plot.ruleY([0.5], { stroke: t.axis }));
    marks.push(Plot.lineY(rows, { x: "t", y: "wp", stroke: t.ink, strokeWidth: 2 }));
    if (!compact) {
      marks.push(
        Plot.text([`${story.home_name || story.home} favored`], {
          frameAnchor: "top-left",
          dx: 8,
          dy: 6,
          fill: t.ink2,
          fontSize: 11,
          fontWeight: 600,
        }),
        Plot.text([`${story.away_name || story.away} favored`], {
          frameAnchor: "bottom-left",
          dx: 8,
          dy: -6,
          fill: t.ink2,
          fontSize: 11,
          fontWeight: 600,
        }),
        Plot.dot(plays, { x: "elapsed", y: "wp_after", r: 9, fill: t.accent, stroke: t.surface, strokeWidth: 2 }),
        Plot.text(plays, {
          x: "elapsed",
          y: "wp_after",
          text: (d: { n: number }) => String(d.n),
          fill: "#ffffff",
          fontSize: 11,
          fontWeight: 700,
        }),
        Plot.axisX({
          ticks: starts,
          tickFormat: (v: number) => labels[starts.indexOf(v)] ?? "",
          textAnchor: "start",
          tickSize: 0,
          dx: 4,
          label: null,
        }),
      );
    }
    if (hover) {
      marks.push(
        Plot.ruleX(rows, Plot.pointerX({ x: "t", stroke: t.muted })),
        Plot.dot(rows, Plot.pointerX({ x: "t", y: "wp", fill: t.ink, r: 4.5, stroke: t.surface, strokeWidth: 2 })),
        Plot.text(
          rows,
          Plot.pointerX({
            px: "t",
            frameAnchor: "top-right",
            dx: -8,
            dy: 6,
            textAnchor: "end",
            lineAnchor: "top",
            fill: t.ink,
            fontSize: 12,
            fontWeight: 500,
            text: (d: Pt) => `${pct(d.wp)}  ${story.home} to win\n${fmtElapsed(d.t)}`,
          }),
        ),
      );
    }

    const plot = Plot.plot({
      width,
      height,
      marginLeft: compact ? 0 : 44,
      marginRight: compact ? 0 : 16,
      marginTop: compact ? 2 : 10,
      marginBottom: compact ? 2 : 28,
      style: {
        background: "transparent",
        color: t.ink2,
        fontFamily: "var(--font-body), system-ui, sans-serif",
        fontSize: compact ? "10px" : "12px",
        overflow: "visible",
      },
      x: { domain: [0, maxT], axis: null },
      y: {
        domain: [0, 1],
        ticks: [0, 0.25, 0.5, 0.75, 1],
        tickFormat: (v: number) => pct(v),
        label: null,
        axis: compact ? null : "left",
        tickSize: 0,
      },
      marks,
    });
    el.replaceChildren(plot);
    onReady?.();
    return () => {
      plot.remove();
    };
  }, [bundle, width, height, mode, variant, onReady]);

  return <div ref={box} className="st-plot" style={{ width: props.width, height }} />;
}
