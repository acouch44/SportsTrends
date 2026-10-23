"use client";

import { useState } from "react";
import type { Social } from "@/lib/bundle";

const PLATFORMS: { key: keyof Social; label: string }[] = [
  { key: "linkedin", label: "LinkedIn" },
  { key: "instagram", label: "Instagram" },
  { key: "tiktok", label: "TikTok" },
  { key: "x", label: "X" },
];

/** Ready-to-paste captions per platform, with the chart link appended. */
export default function CaptionPanel({ social, url }: { social: Social; url: string }) {
  const available = PLATFORMS.filter((p) => typeof social[p.key] === "string" && social[p.key]);
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);
  if (available.length === 0) return null;
  const current = available[Math.min(active, available.length - 1)];
  const body = String(social[current.key]);
  const text = current.key === "x" ? `${body}\n${url}` : `${body}\n\n${url}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable: the textarea is selectable */
    }
  };

  return (
    <section className="captions" aria-labelledby="captions-h">
      <h2 id="captions-h" className="display" style={{ fontSize: "1.5rem", margin: "0 0 10px" }}>
        Post it
      </h2>
      <div className="tabs" role="tablist">
        {available.map((p, i) => (
          <button
            key={p.key}
            role="tab"
            type="button"
            aria-selected={i === active}
            onClick={() => setActive(i)}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="caption-box" role="tabpanel">
        <textarea readOnly value={text} aria-label={`${current.label} caption`} />
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button type="button" className="btn" onClick={copy}>
            {copied ? "Copied" : "Copy caption"}
          </button>
          {!social.reviewed && <span className="share-note">Draft caption, not yet reviewed.</span>}
        </div>
      </div>
    </section>
  );
}
