"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { fmt } from "@/lib/format";
import { theme } from "@/lib/palette";
import { useMode } from "./hooks";
import type { ChartProps } from "./types";

/**
 * Bar-chart race. Pure function of (frames, frame index): the page drives it with a clock and a
 * scrubber, a social render pins the final frame, and a video renderer can pass `frame` per tick.
 */
export default function RaceBar(props: ChartProps) {
  const { bundle, variant = "full", onReady } = props;
  const frames = useMemo(() => bundle.frames ?? [], [bundle.frames]);
  const mode = useMode(props.mode);
  const t = theme(mode);
  const last = Math.max(0, frames.length - 1);
  const controlled = props.frame;
  const [idx, setIdx] = useState(last);
  const [playing, setPlaying] = useState(false);
  const i = Math.min(controlled ?? idx, last);
  const frame = frames[i];

  const compact = variant === "compact";
  const isRender = variant === "render";
  const big = isRender && (props.width ?? 0) >= 900; // phone-sized social canvas
  const rowH = compact ? 20 : big ? 56 : isRender ? 40 : 36;
  const barH = compact ? 12 : big ? 30 : 22;
  const labelW = compact ? 84 : big ? 230 : 150;
  const textPx = big ? 22 : undefined;
  const maxRows = compact ? 7 : Math.max(...frames.map((f) => f.ranks.length), 1);
  const nRows = isRender && props.height ? Math.min(maxRows, Math.floor((props.height - 70) / rowH)) : maxRows;
  const max = Math.max(1, ...(frame?.ranks.map((r) => r.value) ?? [1]));
  const keys = useMemo(() => {
    const s = new Set<string>();
    for (const f of frames) for (const r of f.ranks) s.add(r.key);
    return Array.from(s);
  }, [frames]);
  const vf = fmt(bundle.encoding?.x.format ?? ",.0f");

  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (controlled !== undefined || isRender || compact) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const el = root.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          io.disconnect();
          setIdx(0);
          setPlaying(true);
        }
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [controlled, isRender, compact]);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      setIdx((k) => {
        if (k >= last) {
          setPlaying(false);
          return k;
        }
        return k + 1;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [playing, last]);

  useEffect(() => {
    onReady?.();
  }, [onReady]);

  if (!frame) return null;

  return (
    <div
      ref={root}
      className={`race${compact ? " race-compact" : ""}`}
      style={{ "--row-h": `${rowH}px` } as CSSProperties}
    >
      <div className="race-head" style={{ fontSize: textPx }}>
        {!compact && <span>{bundle.encoding?.x.label}</span>}
        <span className="race-year" style={big ? { fontSize: 80 } : undefined}>
          {frame.t}
        </span>
      </div>
      <div className="race-body" style={{ height: nRows * rowH }}>
        {keys.map((key) => {
          const r = frame.ranks.find((x) => x.key === key);
          const rank = r ? frame.ranks.indexOf(r) : -1;
          const visible = !!r && rank < nRows;
          const pct = r ? (r.value / max) * 100 : 0;
          return (
            <div
              key={key}
              className="race-row"
              aria-hidden={!visible}
              style={{
                transform: `translateY(${(visible ? rank : nRows) * rowH}px)`,
                opacity: visible ? 1 : 0,
                height: rowH,
              }}
            >
              <span className="race-label" style={{ width: labelW, fontSize: textPx }}>
                {r?.label ?? ""}
              </span>
              <span className="race-track" style={big ? { marginRight: 130 } : undefined}>
                <span
                  className="race-bar"
                  style={{ width: `${pct}%`, height: barH, background: r?.color ?? t.accent }}
                />
                <span className="race-value" style={{ left: `calc(${pct}% + 8px)`, fontSize: textPx }}>
                  {r ? vf(r.value) : ""}
                </span>
              </span>
            </div>
          );
        })}
      </div>
      {variant === "full" && controlled === undefined && (
        <div className="race-controls">
          <button
            type="button"
            className="btn"
            onClick={() => {
              if (i >= last && !playing) setIdx(0);
              setPlaying((p) => !p);
            }}
          >
            {playing ? "Pause" : i >= last ? "Replay" : "Play"}
          </button>
          <input
            type="range"
            min={0}
            max={last}
            value={i}
            aria-label="Season"
            onChange={(e) => {
              setPlaying(false);
              setIdx(Number(e.target.value));
            }}
          />
          <span>
            {frames[0]?.t} to {frames[last]?.t}
          </span>
        </div>
      )}
    </div>
  );
}
