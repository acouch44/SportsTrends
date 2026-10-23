import type { Metadata } from "next";
import RenderFrame from "@/components/RenderFrame";
import { chartParams, loadBundle } from "@/lib/registry";
import { FORMATS, FORMAT_KEYS, type Format } from "@/lib/site";

export const dynamicParams = false;
export const metadata: Metadata = { robots: { index: false, follow: false } };

export function generateStaticParams() {
  return chartParams().flatMap((p) => FORMAT_KEYS.map((format) => ({ ...p, format })));
}

export default async function RenderPage({
  params,
}: {
  params: Promise<{ league: string; slug: string; format: string }>;
}) {
  const { league, slug, format } = await params;
  const f = (format in FORMATS ? format : "og") as Format;
  const b = loadBundle(league, slug);
  const { w, h } = FORMATS[f];
  return (
    <div style={{ width: w, height: h, overflow: "hidden" }}>
      <RenderFrame bundle={b} format={f} />
    </div>
  );
}
