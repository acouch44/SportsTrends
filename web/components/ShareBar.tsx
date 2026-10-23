"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { ChartBundle } from "@/lib/bundle";
import { FORMATS, type Format } from "@/lib/site";
import RenderFrame from "./RenderFrame";

const DOWNLOADS: { format: Format; label: string }[] = [
  { format: "square", label: "Square PNG" },
  { format: "portrait", label: "Portrait PNG" },
  { format: "story", label: "Story PNG" },
];

/** Copy link, native share, and client-side PNG exports at social sizes. */
export default function ShareBar({ bundle, url }: { bundle: ChartBundle; url: string }) {
  const [note, setNote] = useState("");
  const [pending, setPending] = useState<Format | null>(null);
  const holder = useRef<HTMLDivElement>(null);
  const canShare = useSyncExternalStore(
    () => () => {},
    () => typeof navigator.share === "function",
    () => false,
  );

  useEffect(() => {
    if (!note) return;
    const id = window.setTimeout(() => setNote(""), 2500);
    return () => window.clearTimeout(id);
  }, [note]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setNote("Link copied");
    } catch {
      setNote(url);
    }
  };

  const share = async () => {
    try {
      await navigator.share({ title: bundle.title, text: bundle.hook, url });
    } catch {
      /* dismissed */
    }
  };

  const capture = useCallback(async () => {
    const format = pending;
    const node = holder.current?.querySelector<HTMLElement>(".rf");
    if (!format || !node) return;
    try {
      const { toPng } = await import("html-to-image");
      const { w, h } = FORMATS[format];
      const dataUrl = await toPng(node, { width: w, height: h, pixelRatio: 1, cacheBust: false });
      const a = document.createElement("a");
      a.href = dataUrl;
      a.download = `${bundle.league}-${bundle.slug}-${format}.png`;
      a.click();
      setNote(`${FORMATS[format].label} image saved`);
    } catch (e) {
      console.error(e);
      setNote("Could not render the image in this browser");
    } finally {
      setPending(null);
    }
  }, [pending, bundle.league, bundle.slug]);

  return (
    <div className="share" role="group" aria-label="Share this chart">
      <button type="button" className="btn btn-primary" onClick={copy}>
        Copy link
      </button>
      {canShare && (
        <button type="button" className="btn" onClick={share}>
          Share
        </button>
      )}
      {DOWNLOADS.map((d) => (
        <button
          key={d.format}
          type="button"
          className="btn"
          disabled={pending !== null}
          onClick={() => setPending(d.format)}
        >
          {pending === d.format ? "Rendering" : d.label}
        </button>
      ))}
      <span className="share-note" aria-live="polite">
        {note}
      </span>
      {pending && (
        <div
          ref={holder}
          aria-hidden
          style={{ position: "fixed", left: -20000, top: 0, pointerEvents: "none", zIndex: -1 }}
        >
          <RenderFrame bundle={bundle} format={pending} onReady={capture} />
        </div>
      )}
    </div>
  );
}
