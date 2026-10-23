/**
 * Colour tokens. Series colours are the validated reference categorical palette from the dataviz
 * method (adjacent pairs clear the colour-vision gates in both modes; the first three slots clear
 * all pairs). Chrome colours are this site's own: cool paper and navy ink in light mode, a night
 * navy in dark mode. Keep chart text in ink tokens, never in a series colour.
 */

export type Mode = "light" | "dark";

export const SERIES: Record<Mode, string[]> = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
  dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
};

/** One-hue sequential ramp (blue), light -> dark, for heat maps. */
export const SEQUENTIAL: Record<Mode, string[]> = {
  light: ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
  dark: ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"],
};

export interface Chrome {
  page: string;
  surface: string;
  ink: string;
  ink2: string;
  muted: string;
  grid: string;
  axis: string;
  accent: string;
  wash: string;
  deemphasis: string;
}

export const CHROME: Record<Mode, Chrome> = {
  light: {
    page: "#f3f4f1",
    surface: "#ffffff",
    ink: "#0f1c2e",
    ink2: "#4f5b6b",
    muted: "#8a94a0",
    grid: "#e6e8e4",
    axis: "#c9cdc8",
    accent: "#1c5cab",
    wash: "#eaf1fb",
    deemphasis: "#b4bac2",
  },
  dark: {
    page: "#0b1220",
    surface: "#121b2b",
    ink: "#eef1f5",
    ink2: "#b6bfcb",
    muted: "#7e8896",
    grid: "#243044",
    axis: "#34435a",
    accent: "#6da7ec",
    wash: "#1a2a44",
    deemphasis: "#4d5969",
  },
};

export function theme(mode: Mode) {
  return { mode, ...CHROME[mode], series: SERIES[mode], sequential: SEQUENTIAL[mode] };
}
export type Theme = ReturnType<typeof theme>;

/** Resolve a bundle series colour: an explicit hex wins, otherwise the palette slot. */
export function seriesColor(t: Theme, declared: string | null | undefined, slot: number): string {
  if (declared && /^#[0-9a-f]{6}$/i.test(declared)) return declared;
  return t.series[slot % t.series.length];
}
