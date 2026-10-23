import type { Kind } from "./bundle";

/** Default page height per chart kind (race bars and small multiples size themselves). */
export function pageHeight(kind: Kind): number | undefined {
  switch (kind) {
    case "line":
    case "area":
      return 460;
    case "wp_story":
      return 420;
    case "heatmap":
      return 520;
    default:
      return undefined;
  }
}
