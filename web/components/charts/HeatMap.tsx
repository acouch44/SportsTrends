"use client";

import * as Plot from "@observablehq/plot";
import { useEffect, useRef } from "react";
import { fmt } from "@/lib/format";
import { theme } from "@/lib/palette";
import { useMode, useSize } from "./hooks";
import type { ChartProps } from "./types";

interface Cell {
  x: number;
  y: number;
  n: number;
  v: number;
}

type Pt = [number, number];

function arc(cx: number, cy: number, r: number, a0: number, a1: number, steps = 48): Pt[] {
  return Array.from({ length: steps + 1 }, (_, i) => {
    const a = a0 + ((a1 - a0) * i) / steps;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
}

/** NBA half court in NBA.com shot-chart units: tenths of a foot, basket at the origin. */
function nbaHalfCourt(): Pt[][] {
  const base = -52.5;
  const half = 417.5;
  const cornerY = Math.sqrt(237.5 ** 2 - 220 ** 2); // the 22 ft corner line meets the 23.75 ft arc
  const a0 = Math.atan2(cornerY, 220);
  return [
    [
      [-250, base],
      [250, base],
      [250, half],
      [-250, half],
      [-250, base],
    ],
    [
      [-80, base],
      [-80, 137.5],
      [80, 137.5],
      [80, base],
    ],
    arc(0, 137.5, 60, 0, Math.PI),
    [
      [-30, -12.5],
      [30, -12.5],
    ],
    arc(0, 0, 7.5, 0, 2 * Math.PI),
    arc(0, 0, 40, 0, Math.PI),
    [[-220, base], [-220, cornerY], ...arc(0, 0, 237.5, Math.PI - a0, a0), [220, cornerY], [220, base]],
    arc(0, half, 60, Math.PI, 2 * Math.PI),
  ];
}

const COURTS: Record<string, () => Pt[][]> = { nba_halfcourt: nbaHalfCourt };

/**
 * Binned values on a court. One hue light-to-dark for a magnitude; two hues through a neutral
 * grey when the values are a change (any negative cell). The colour domain is clamped at the
 * 98th percentile of |value| so one extreme cell cannot wash out the rest.
 */
export default function HeatMap(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const box = useRef<HTMLDivElement>(null);
  const mode = useMode(props.mode);
  const { width, height } = useSize(box, { width: props.width, height: props.height ?? 520 });

  useEffect(() => {
    const el = box.current;
    const grid = bundle.grid;
    if (!el || !width || !height || !grid) return;
    const t = theme(mode);
    const cells: Cell[] = grid.cells.map(([x, y, n, v]) => ({ x, y, n, v: v ?? n }));
    const compact = variant === "compact";
    const big = variant === "render" && width >= 900;
    const legend = !compact;
    const legendH = legend ? (big ? 52 : 40) : 0;
    const margin = compact ? 2 : 12;
    const [x0, x1] = grid.x_range;
    const [y0, y1] = grid.y_range;
    const innerW = Math.max(1, width - margin * 2);
    const innerH = Math.max(1, height - legendH - margin * 2);
    const pxPerUnit = Math.min(innerW / (x1 - x0), innerH / (y1 - y0));
    const padX = (innerW / pxPerUnit - (x1 - x0)) / 2;
    const padY = (innerH / pxPerUnit - (y1 - y0)) / 2;
    const r = Math.max(1.5, 0.53 * grid.bin_width * pxPerUnit);
    const vf = fmt(bundle.encoding?.y.format ?? ",.0f");
    const unit = grid.value_label ? ` ${grid.value_label}` : "";
    const label = bundle.encoding?.y.label || grid.value_label || null;

    const abs = cells.map((c) => Math.abs(c.v)).sort((a, b) => a - b);
    const m = abs[Math.min(abs.length - 1, Math.floor(abs.length * 0.98))] || 1;
    const diverging = cells.some((c) => c.v < 0);
    const color: Plot.ScaleOptions = diverging
      ? { type: "diverging", domain: [-m, m], pivot: 0, range: t.diverging, interpolate: "rgb", clamp: true }
      : { type: "linear", domain: [0, m], range: t.sequential, interpolate: "rgb", clamp: true };

    const marks: Plot.Markish[] = [];
    if (grid.shape === "hex") {
      marks.push(
        Plot.dot(cells, {
          x: "x",
          y: "y",
          r,
          symbol: "hexagon",
          fill: "v",
          stroke: t.surface,
          strokeWidth: compact ? 0.5 : 1,
        }),
      );
    } else {
      marks.push(
        Plot.rect(cells, {
          x1: (d: Cell) => d.x - grid.bin_width / 2,
          x2: (d: Cell) => d.x + grid.bin_width / 2,
          y1: (d: Cell) => d.y - grid.bin_width / 2,
          y2: (d: Cell) => d.y + grid.bin_width / 2,
          fill: "v",
          inset: 1,
        }),
      );
    }
    const court = grid.court ? COURTS[grid.court]?.() : undefined;
    if (court) {
      for (const line of court) {
        marks.push(Plot.line(line, { stroke: t.ink2, strokeWidth: compact ? 0.8 : big ? 2 : 1.3, strokeOpacity: 0.7 }));
      }
    }
    if (variant === "full" || variant === "panel") {
      marks.push(
        Plot.tip(
          cells,
          Plot.pointer({
            x: "x",
            y: "y",
            maxRadius: r * 1.2,
            title: (d: Cell) => `${vf(d.v)}${unit}\n${d.n.toLocaleString()} shots`,
            fill: t.surface,
            stroke: t.axis,
          }),
        ),
      );
    }

    const plot = Plot.plot({
      width,
      height: height - legendH,
      margin,
      style: {
        background: "transparent",
        color: t.ink2,
        fontFamily: "var(--font-body), system-ui, sans-serif",
        fontSize: big ? "15px" : "12px",
        overflow: "visible",
      },
      x: { domain: [x0 - padX, x1 + padX], axis: null },
      y: { domain: [y0 - padY, y1 + padY], axis: null },
      color,
      marks,
    });
    el.replaceChildren();
    if (legend) {
      const key = Plot.legend({
        color: { ...color, label },
        width: Math.min(big ? 420 : 280, width),
        height: legendH - 6,
        marginLeft: 0,
        style: { color: t.ink2, fontFamily: "var(--font-body), system-ui, sans-serif", fontSize: big ? "15px" : "12px" },
      });
      el.appendChild(key);
    }
    el.appendChild(plot);
    onReady?.();
    return () => {
      plot.remove();
    };
  }, [bundle, width, height, mode, variant, onReady]);

  return <div ref={box} className="st-plot" style={{ width: props.width, height }} />;
}
