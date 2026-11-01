"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import type { ChartBundle } from "@/lib/bundle";

/** Copy link and native share. The link itself carries the social image via its Open Graph tags. */
export default function ShareBar({ bundle, url }: { bundle: ChartBundle; url: string }) {
  const [note, setNote] = useState("");
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
      <span className="share-note" aria-live="polite">
        {note}
      </span>
    </div>
  );
}
