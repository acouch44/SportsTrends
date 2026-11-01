import type { ChartBundle } from "@/lib/bundle";
import type { Mode } from "@/lib/palette";

/**
 * full    - the chart page: axes, direct labels, hover readout, controls
 * render  - a social PNG: like full but static, at an exact width and height
 * panel   - one cell of a small-multiples grid
 * compact - a gallery tile: marks only, no axes or text
 */
export type Variant = "full" | "render" | "panel" | "compact";

export interface ChartProps {
  bundle: ChartBundle;
  variant?: Variant;
  mode?: Mode;
  width?: number;
  height?: number;
  /** race bars: show this frame instead of running their own clock */
  frame?: number;
  /** called once the marks are in the DOM (the render route waits for it) */
  onReady?: () => void;
}
