"use client";

import HeatMap from "./HeatMap";
import RaceBar from "./RaceBar";
import SmallMultiples from "./SmallMultiples";
import TrendLine from "./TrendLine";
import WpStory from "./WpStory";
import type { ChartProps } from "./types";

/** Dispatch a bundle to the component for its kind. */
export default function Chart(props: ChartProps) {
  switch (props.bundle.kind) {
    case "line":
    case "area":
      return <TrendLine {...props} />;
    case "small_multiples":
      return <SmallMultiples {...props} />;
    case "race":
      return <RaceBar {...props} />;
    case "wp_story":
      return <WpStory {...props} />;
    case "heatmap":
      return <HeatMap {...props} />;
  }
}
