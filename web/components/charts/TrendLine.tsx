"use client";

import * as Plot from "@observablehq/plot";
import { useEffect, useRef } from "react";
import { col, type ChartBundle } from "@/lib/bundle";
import { fmt } from "@/lib/format";
import { seriesColor, theme } from "@/lib/palette";
import { useMode, useSize } from "./hooks";
import type { ChartProps } from "./types";

interface Row {
  x: number;
  y: number;
  s: string;
}

export function trendRows(b: ChartBundle): Row[] {
  if (!b.data || !b.encoding) return [];
  const t = b.data;
  const xi = col(t, b.encoding.x.field);
  const yi = col(t, b.encoding.y.field);
  const si = b.encoding.series ? t.columns.indexOf(b.encoding.series.field) : -1;
  const out: Row[] = [];
  for (const r of t.rows) {
    const y = r[yi];
    if (y == null) continue;
    out.push({ x: Number(r[xi]), y: Number(y), s: si >= 0 ? String(r[si]) : "value" });
  }
  return out;
}

/** Line and area charts: multi-series over a numeric x (seasons), with annotations. */
export default function TrendLine(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const box = useRef<HTMLDivElement>(null);
  const mode = useMode(props.mode);
  const { width, height } = useSize(box, { width: props.width, height: props.height ?? 420 });

  useEffect(() => {
    const el = box.current;
    if (!el || !width || !height || !bundle.encoding) return;
    const t = theme(mode);
    const enc = bundle.encoding;
    const rows = trendRows(bundle);
    const defs = bundle.series.length
      ? bundle.series
      : [{ key: "value", label: bundle.title, color: undefined, emphasis: true }];
    const keys = defs.map((d) => d.key);
    const colors = defs.map((d, i) => seriesColor(t, d.color, i));
    const label = new Map(defs.map((d) => [d.key, d.label]));
    const fx = fmt(enc.x.format ?? "d");
    const fy = fmt(enc.y.format);
    const compact = variant === "compact";
    const panel = variant === "panel";
    const hover = variant === "full" || panel;
    const multi = keys.length > 1;
    const yDomain = bundle.domain?.y;
    const xDomain = bundle.domain?.x?.map(Number);

    const byX = new Map<number, Record<string, number>>();
    for (const r of rows) {
      let o = byX.get(r.x);
      if (!o) byX.set(r.x, (o = {}));
      o[r.s] = r.y;
    }
    const pivot = Array.from(byX, ([x, values]) => ({ x, values })).sort((a, b) => a.x - b.x);
    const vlines = bundle.annotations.filter((a) => a.kind === "vline" && typeof a.x === "number");
    const points = bundle.annotations.filter(
      (a) => a.kind === "point" && typeof a.x === "number" && typeof a.y === "number",
    );

    // phone-sized social canvases need bigger type than the page does
    const big = variant === "render" && width >= 900;
    const fontSize = compact ? 10 : panel ? 11 : big ? 15 : 12;
    const noteSize = big ? 14 : 11;
    const lineWidth = big ? 2.5 : 2;
    const xs = rows.map((r) => r.x);
    const xMin = xDomain?.[0] ?? Math.min(...xs);
    const xMax = xDomain?.[1] ?? Math.max(...xs);
    const rightThird = xMin + (xMax - xMin) * 0.66;

    const mL = compact ? 0 : panel ? 38 : big ? 56 : 46;
    const mR = compact ? 0 : panel ? 12 : multi ? (big ? 200 : 150) : 24;
    const plotW = Math.max(1, width - mL - mR);
    const px = (x: number) => mL + ((x - xMin) / Math.max(1e-9, xMax - xMin)) * plotW;
    // annotation labels: right-third ones hang left (off the end-labels); rows are assigned
    // greedily so labels for neighbouring years never overlap
    const placed: { l: number; r: number; row: number }[] = [];
    const notes = vlines.map((a) => {
      const x = a.x as number;
      const flip = x >= rightThird;
      const w = a.label.length * noteSize * 0.56 + 8;
      const l = flip ? px(x) - w : px(x);
      const r = l + w;
      let row = 0;
      while (row < 4 && placed.some((p) => p.row === row && l < p.r && r > p.l)) row++;
      placed.push({ l, r, row });
      return { flip, row };
    });
    const noteRows = notes.length ? Math.max(...notes.map((n) => n.row)) + 1 : 0;
    const rowStep = noteSize + 3;

    const marks: Plot.Markish[] = [];
    if (!compact) marks.push(Plot.gridY({ stroke: t.grid, strokeOpacity: 1 }));
    if (!compact && yDomain && yDomain[0] <= 0) marks.push(Plot.ruleY([0], { stroke: t.axis }));
    if (!compact) {
      vlines.forEach((a, i) => {
        marks.push(Plot.ruleX([a.x as number], { stroke: t.axis }));
        if (!panel) {
          const { flip, row } = notes[i];
          marks.push(
            Plot.text([a], {
              x: "x",
              text: "label",
              frameAnchor: "top",
              dy: 2 + row * rowStep,
              dx: flip ? -5 : 5,
              textAnchor: flip ? "end" : "start",
              lineAnchor: "top",
              fill: t.ink2,
              fontSize: noteSize,
            }),
          );
        }
      });
    }
    if (bundle.kind === "area") {
      marks.push(Plot.areaY(rows, { x: "x", y: "y", z: "s", fill: "s", fillOpacity: 0.1 }));
    }
    marks.push(
      Plot.lineY(rows, {
        x: "x",
        y: "y",
        z: "s",
        stroke: "s",
        strokeWidth: lineWidth,
        strokeLinejoin: "round",
        strokeLinecap: "round",
      }),
    );
    if (!compact && !panel && multi) {
      marks.push(
        Plot.text(
          rows,
          Plot.selectLast({
            x: "x",
            y: "y",
            z: "s",
            text: (d: Row) => label.get(d.s) ?? d.s,
            dx: 8,
            textAnchor: "start",
            fill: t.ink,
            fontSize,
            fontWeight: 600,
          }),
        ),
      );
    }
    if (!compact) {
      for (const a of points) {
        marks.push(
          Plot.dot([a], { x: "x", y: "y", r: big ? 6 : 5, fill: colors[0], stroke: t.surface, strokeWidth: 2 }),
        );
        if (!panel) {
          marks.push(
            Plot.text([a], {
              x: "x",
              y: "y",
              text: (d: { label: string; y: number }) => `${d.label} ${fy(d.y)}`.trim(),
              dy: -14,
              fill: t.ink,
              fontSize: noteSize,
              fontWeight: 600,
            }),
          );
        }
      }
    }
    if (hover) {
      marks.push(Plot.ruleX(pivot, Plot.pointerX({ x: "x", stroke: t.muted })));
      marks.push(
        Plot.dot(
          rows,
          Plot.pointerX({ x: "x", y: "y", z: "s", fill: "s", r: 4.5, stroke: t.surface, strokeWidth: 2 }),
        ),
      );
      marks.push(
        Plot.text(
          pivot,
          Plot.pointerX({
            px: "x",
            frameAnchor: "top-left",
            dx: 8,
            dy: 8,
            textAnchor: "start",
            lineAnchor: "top",
            fill: t.ink,
            fontSize: 12,
            fontWeight: 500,
            text: (d: { x: number; values: Record<string, number> }) =>
              [
                fx(d.x),
                ...keys.filter((k) => d.values[k] != null).map((k) => `${fy(d.values[k])}  ${label.get(k)}`),
              ].join("\n"),
          }),
        ),
      );
    }

    const plot = Plot.plot({
      width,
      height,
      marginLeft: mL,
      marginRight: mR,
      marginTop: compact ? 2 : panel ? 8 : noteRows ? 10 + noteRows * rowStep : 16,
      marginBottom: compact ? 2 : big ? 34 : 28,
      style: {
        background: "transparent",
        color: t.ink2,
        fontFamily: "var(--font-body), system-ui, sans-serif",
        fontSize: `${fontSize}px`,
        overflow: "visible",
      },
      x: {
        domain: xDomain,
        tickFormat: (v: number) => fx(v),
        label: null,
        axis: compact ? null : "bottom",
        tickSize: 0,
        ticks: panel ? 4 : undefined,
      },
      y: {
        domain: yDomain,
        tickFormat: (v: number) => fy(v),
        label: null,
        axis: compact ? null : "left",
        tickSize: 0,
        nice: !yDomain,
        ticks: panel ? 4 : 6,
      },
      color: { domain: keys, range: colors },
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
