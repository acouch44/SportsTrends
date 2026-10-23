/**
 * zod mirror of src/sportstrends/bundle.py. The Python side drops null fields on write, so
 * optional fields are `.optional()` here rather than nullable.
 */
import { z } from "zod";

export const Kind = z.enum(["line", "area", "heatmap", "race", "small_multiples", "wp_story"]);
export type Kind = z.infer<typeof Kind>;

const Axis = z.object({
  field: z.string(),
  type: z.enum(["quantitative", "temporal", "ordinal", "nominal"]).default("quantitative"),
  label: z.string().default(""),
  format: z.string().optional(),
});

const Encoding = z.object({
  x: Axis,
  y: Axis,
  series: Axis.optional(),
  facet: Axis.optional(),
});

const Domain = z.object({
  x: z.array(z.union([z.number(), z.string()])).optional(),
  y: z.array(z.number()).optional(),
});

const Series = z.object({
  key: z.string(),
  label: z.string(),
  color: z.string().optional(),
  emphasis: z.boolean().default(false),
});

const Annotation = z.object({
  kind: z.enum(["vline", "hline", "point", "range", "text"]),
  x: z.union([z.number(), z.string()]).optional(),
  y: z.number().optional(),
  x2: z.union([z.number(), z.string()]).optional(),
  label: z.string().default(""),
  note: z.string().optional(),
});

const Source = z.object({
  name: z.string(),
  url: z.string(),
  license: z.string().default(""),
  attribution: z.string().default(""),
});

export const Social = z.object({
  hook: z.string().default(""),
  alt_text: z.string().default(""),
  linkedin: z.string().default(""),
  instagram: z.string().default(""),
  tiktok: z.string().default(""),
  x: z.string().default(""),
  hashtags: z.array(z.string()).default([]),
  reviewed: z.boolean().default(false),
  generated_for: z.string().default(""),
});
export type Social = z.infer<typeof Social>;

const Table = z.object({
  columns: z.array(z.string()),
  rows: z.array(z.array(z.unknown())),
});
export type Table = z.infer<typeof Table>;

const Grid = z.object({
  shape: z.enum(["hex", "rect"]).default("hex"),
  bin_width: z.number(),
  x_range: z.array(z.number()),
  y_range: z.array(z.number()),
  court: z.string().optional(),
  value_label: z.string().default(""),
  cells: z.array(z.array(z.number())),
});

const RankItem = z.object({
  key: z.string(),
  label: z.string(),
  value: z.number(),
  color: z.string().optional(),
  group: z.string().optional(),
});
export type RankItem = z.infer<typeof RankItem>;

const Frame = z.object({ t: z.string(), ranks: z.array(RankItem) });
export type Frame = z.infer<typeof Frame>;

const Facet = z.object({ key: z.string(), label: z.string() });

const KeyPlay = z.object({
  elapsed: z.number(),
  qtr: z.number(),
  clock: z.string(),
  wp_before: z.number(),
  wp_after: z.number(),
  desc: z.string(),
  score: z.string(),
});
export type KeyPlay = z.infer<typeof KeyPlay>;

const Story = z.object({
  game_id: z.string(),
  season: z.number(),
  week: z.number(),
  date: z.string(),
  home: z.string(),
  away: z.string(),
  home_name: z.string().default(""),
  away_name: z.string().default(""),
  home_color: z.string().default("#444444"),
  away_color: z.string().default("#999999"),
  final: z.string().default(""),
  excitement: z.number().default(0),
  key_plays: z.array(KeyPlay).default([]),
});
export type Story = z.infer<typeof Story>;

export const ChartBundle = z.object({
  schema_version: z.number().default(1),
  id: z.string(),
  league: z.string(),
  slug: z.string(),
  kind: Kind,
  title: z.string(),
  subtitle: z.string().default(""),
  hook: z.string().default(""),
  tags: z.array(z.string()).default([]),
  source: Source,
  generated_at: z.string(),
  data_through: z.string(),
  code_version: z.string().default(""),
  encoding: Encoding.optional(),
  domain: Domain.optional(),
  series: z.array(Series).default([]),
  annotations: z.array(Annotation).default([]),
  data: Table.optional(),
  grid: Grid.optional(),
  frames: z.array(Frame).optional(),
  facets: z.array(Facet).optional(),
  story: Story.optional(),
  social: Social.default(() => Social.parse({})),
  summary: z.record(z.string(), z.unknown()).default({}),
});
export type ChartBundle = z.infer<typeof ChartBundle>;

export const RegistryEntry = z.object({
  id: z.string(),
  league: z.string(),
  slug: z.string(),
  kind: Kind,
  title: z.string(),
  subtitle: z.string().default(""),
  hook: z.string().default(""),
  tags: z.array(z.string()).default([]),
  data_through: z.string(),
  generated_at: z.string(),
});
export type RegistryEntry = z.infer<typeof RegistryEntry>;

export const Registry = z.object({
  schema_version: z.number().default(1),
  generated_at: z.string(),
  charts: z.array(RegistryEntry),
});
export type Registry = z.infer<typeof Registry>;

/** Column index helper for the column-oriented table. */
export function col(table: Table, name: string): number {
  const i = table.columns.indexOf(name);
  if (i < 0) throw new Error(`bundle table has no column "${name}" (has ${table.columns.join(", ")})`);
  return i;
}
