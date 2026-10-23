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

/** Binned density on a court/rink/field: one hue, light to dark. */
export default function HeatMap(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const box = useRef<HTMLDivElement>(null);
  const mode = useMode(props.mode);
  const { width, height } = useSize(box, { width: props.width, height: props.height ?? 420 });

  useEffect(() => {
    const el = box.current;
    const grid = bundle.grid;
    if (!el || !width || !height || !grid) return;
    const t = theme(mode);
    const cells: Cell[] = grid.cells.map(([x, y, n, v]) => ({ x, y, n, v: v ?? n }));
    const compact = variant === "compact";
    const [x0, x1] = grid.x_range;
    const [y0, y1] = grid.y_range;
    const margin = compact ? 0 : 20;
    const pxPerUnit = Math.min((width - margin * 2) / (x1 - x0), (height - margin * 2) / (y1 - y0));
    const r = Math.max(1.5, (grid.bin_width / 2) * pxPerUnit);
    const vf = fmt(bundle.encoding?.y.format ?? ",.0f");

    const marks: Plot.Markish[] =
      grid.shape === "hex"
        ? [
            Plot.dot(cells, {
              x: "x",
              y: "y",
              r,
              symbol: "hexagon",
              fill: "v",
              stroke: t.surface,
              strokeWidth: 1,
              title: compact ? undefined : (d: Cell) => `${vf(d.v)}${grid.value_label ? ` ${grid.value_label}` : ""}`,
            }),
          ]
        : [
            Plot.rect(cells, {
              x1: (d: Cell) => d.x - grid.bin_width / 2,
              x2: (d: Cell) => d.x + grid.bin_width / 2,
              y1: (d: Cell) => d.y - grid.bin_width / 2,
              y2: (d: Cell) => d.y + grid.bin_width / 2,
              fill: "v",
              inset: 1,
              title: compact ? undefined : (d: Cell) => vf(d.v),
            }),
          ];

    const plot = Plot.plot({
      width,
      height,
      margin,
      style: { background: "transparent", color: t.ink2, overflow: "visible" },
      x: { domain: [x0, x1], axis: null },
      y: { domain: [y0, y1], axis: null },
      color: { type: "linear", range: t.sequential, legend: !compact, label: grid.value_label || null },
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
