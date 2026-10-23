import type { ChartBundle } from "@/lib/bundle";
import { fmt, fmtElapsed } from "@/lib/format";

/** The table-view twin of a chart: every plotted value, reachable without hover or colour. */
export default function DataTable({ bundle }: { bundle: ChartBundle }) {
  if (bundle.kind === "race" && bundle.frames?.length) {
    const last = bundle.frames[bundle.frames.length - 1];
    const vf = fmt(bundle.encoding?.x.format ?? ",.0f");
    return (
      <details className="data-table">
        <summary>Data table: standings after {last.t}</summary>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th style={{ textAlign: "left" }}>{bundle.encoding?.y.label || "Name"}</th>
              <th>{bundle.encoding?.x.label || "Value"}</th>
            </tr>
          </thead>
          <tbody>
            {last.ranks.map((r, i) => (
              <tr key={r.key}>
                <td style={{ textAlign: "left" }}>{i + 1}</td>
                <td style={{ textAlign: "left" }}>
                  {r.label}
                  {r.group ? ` (${r.group})` : ""}
                </td>
                <td>{vf(r.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    );
  }

  if (bundle.kind === "wp_story" && bundle.story) {
    const pct = fmt(".0%");
    return (
      <details className="data-table">
        <summary>Data table: biggest swings</summary>
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>When</th>
              <th>Before</th>
              <th>After</th>
              <th style={{ textAlign: "left" }}>Play</th>
            </tr>
          </thead>
          <tbody>
            {bundle.story.key_plays.map((k) => (
              <tr key={k.elapsed}>
                <td style={{ textAlign: "left" }}>{fmtElapsed(k.elapsed)}</td>
                <td>{pct(k.wp_before)}</td>
                <td>{pct(k.wp_after)}</td>
                <td style={{ textAlign: "left" }}>{k.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    );
  }

  if (!bundle.data || !bundle.encoding) return null;
  const { columns, rows } = bundle.data;
  const xi = columns.indexOf(bundle.encoding.x.field);
  const yi = columns.indexOf(bundle.encoding.y.field);
  const si = bundle.encoding.series ? columns.indexOf(bundle.encoding.series.field) : -1;
  const fi = bundle.encoding.facet ? columns.indexOf(bundle.encoding.facet.field) : -1;
  const fx = fmt(bundle.encoding.x.format ?? "d");
  const fy = fmt(bundle.encoding.y.format);
  const seriesLabel = new Map(bundle.series.map((s) => [s.key, s.label]));
  const facetLabel = new Map((bundle.facets ?? []).map((f) => [f.key, f.label]));
  const xs = Array.from(new Set(rows.map((r) => Number(r[xi])))).sort((a, b) => a - b);
  const groups = Array.from(
    new Set(rows.map((r) => `${fi >= 0 ? r[fi] : ""}\u0000${si >= 0 ? r[si] : ""}`)),
  );
  const cell = new Map<string, number>();
  for (const r of rows) {
    cell.set(`${r[xi]}\u0000${fi >= 0 ? r[fi] : ""}\u0000${si >= 0 ? r[si] : ""}`, Number(r[yi]));
  }
  const header = (g: string) => {
    const [f, s] = g.split("\u0000");
    return [f ? (facetLabel.get(f) ?? f) : "", s ? (seriesLabel.get(s) ?? s) : ""].filter(Boolean).join(": ") || bundle.encoding!.y.label;
  };

  return (
    <details className="data-table">
      <summary>Data table</summary>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>{bundle.encoding.x.label || bundle.encoding.x.field}</th>
              {groups.map((g) => (
                <th key={g}>{header(g)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {xs.map((x) => (
              <tr key={x}>
                <td>{fx(x)}</td>
                {groups.map((g) => {
                  const v = cell.get(`${x}\u0000${g}`);
                  return <td key={g}>{v == null || Number.isNaN(v) ? "" : fy(v)}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
