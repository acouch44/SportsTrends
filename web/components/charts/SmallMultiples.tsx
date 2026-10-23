"use client";

import { useCallback, useRef } from "react";
import TrendLine from "./TrendLine";
import type { ChartProps } from "./types";

/** One small line chart per facet, sharing the bundle's y domain. */
export default function SmallMultiples(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const facets = bundle.facets ?? [];
  const n = facets.length;
  const done = useRef(0);
  const ready = useCallback(() => {
    done.current += 1;
    if (done.current >= n) onReady?.();
  }, [n, onReady]);

  if (variant === "compact") {
    return <TrendLine {...props} facet={facets[0]?.key} />;
  }

  const isRender = variant === "render";
  const cols = isRender ? (props.width && props.width >= 1000 ? Math.min(n, 5) : 2) : undefined;
  const rowsCount = cols ? Math.ceil(n / cols) : 1;
  const panelH = isRender && props.height ? Math.min(360, Math.floor((props.height - 30 * rowsCount) / rowsCount)) : 200;

  return (
    <div
      className="sm-grid"
      style={cols ? { gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` } : undefined}
    >
      {facets.map((f) => (
        <div key={f.key}>
          <div className="sm-label">{f.label}</div>
          <TrendLine
            bundle={bundle}
            facet={f.key}
            mode={props.mode}
            variant="panel"
            height={panelH}
            onReady={ready}
          />
        </div>
      ))}
    </div>
  );
}
