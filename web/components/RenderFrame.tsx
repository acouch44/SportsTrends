"use client";

import { useCallback, useRef, useState } from "react";
import type { ChartBundle } from "@/lib/bundle";
import { longDate } from "@/lib/format";
import { FORMATS, LEAGUES, SITE_NAME, hostLabel, type Format, type League } from "@/lib/site";
import Chart from "./charts/Chart";
import Legend from "./charts/Legend";
import { useSize } from "./charts/hooks";

/**
 * A chart laid out at an exact pixel size for a PNG: title, hook, chart, source line.
 * Always the light theme. Sets data-render-ready="1" once the chart has drawn and fonts loaded.
 */
export default function RenderFrame({
  bundle,
  format,
  onReady,
}: {
  bundle: ChartBundle;
  format: Format;
  onReady?: () => void;
}) {
  const { w, h } = FORMATS[format];
  const box = useRef<HTMLDivElement>(null);
  const size = useSize(box);
  const [ready, setReady] = useState(false);
  const handleReady = useCallback(() => {
    const fonts = typeof document !== "undefined" ? document.fonts?.ready : undefined;
    (fonts ?? Promise.resolve()).then(() => {
      setReady(true);
      onReady?.();
    });
  }, [onReady]);

  const story = format === "story";
  const og = format === "og";
  const pad = og ? 44 : 64;
  const titleSize = og ? 46 : story ? 82 : 64;
  const hookSize = og ? 20 : story ? 34 : 27;
  const footSize = og ? 15 : story ? 24 : 20;
  const headSize = og ? 15 : story ? 24 : 20;
  const league = (LEAGUES as Record<string, string>)[bundle.league] ?? bundle.league.toUpperCase();

  return (
    <div
      className="theme-light rf"
      data-render-ready={ready ? "1" : "0"}
      style={{
        width: w,
        height: h,
        padding: pad,
        paddingTop: story ? pad + 170 : pad,
        paddingBottom: story ? pad + 290 : pad,
      }}
    >
      <header className="rf-head" style={{ fontSize: headSize }}>
        <span className="league-tag">{league}</span>
        <span>{SITE_NAME}</span>
      </header>
      <h1 className="display rf-title" style={{ fontSize: titleSize }}>
        {bundle.title}
      </h1>
      <p className="rf-hook" style={{ fontSize: hookSize }}>
        {bundle.hook || bundle.subtitle}
      </p>
      <Legend bundle={bundle} mode="light" />
      <div ref={box} className="rf-chart" style={story ? { maxHeight: 1040, marginBottom: "auto" } : undefined}>
        {size.width > 0 && size.height > 0 && (
          <Chart
            bundle={bundle}
            mode="light"
            variant="render"
            width={size.width}
            height={size.height}
            onReady={handleReady}
          />
        )}
      </div>
      <footer className="rf-foot" style={{ fontSize: footSize }}>
        <span>
          {bundle.source.attribution || `Data: ${bundle.source.name}`}. Through {longDate(bundle.data_through)}.
        </span>
        <span>
          <strong>{hostLabel()}</strong>/{bundle.league as League}/{bundle.slug}
        </span>
      </footer>
    </div>
  );
}
