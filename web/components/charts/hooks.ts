"use client";

import { useEffect, useLayoutEffect, useState, type RefObject } from "react";
import type { Mode } from "@/lib/palette";

/** Measure an element; a dimension passed in `fixed` is used as-is instead of measured. */
export function useSize(
  ref: RefObject<HTMLElement | null>,
  fixed?: { width?: number; height?: number },
): { width: number; height: number } {
  const fw = fixed?.width;
  const fh = fixed?.height;
  const [size, setSize] = useState({ width: fw ?? 0, height: fh ?? 0 });
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || (fw && fh)) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      const w = fw ?? Math.round(r.width);
      const h = fh ?? Math.round(r.height);
      setSize((s) => (s.width === w && s.height === h ? s : { width: w, height: h }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, fw, fh]);
  return fw && fh ? { width: fw, height: fh } : size;
}

/** Light or dark: a forced value, else the <html data-theme> stamp, else the OS preference. */
export function useMode(forced?: Mode): Mode {
  const [mode, setMode] = useState<Mode>(forced ?? "light");
  useEffect(() => {
    if (forced) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => {
      const stamp = document.documentElement.dataset.theme;
      setMode(stamp === "dark" ? "dark" : stamp === "light" ? "light" : mq.matches ? "dark" : "light");
    };
    read();
    mq.addEventListener("change", read);
    return () => mq.removeEventListener("change", read);
  }, [forced]);
  return forced ?? mode;
}
