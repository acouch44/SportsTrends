"""Where NBA shots moved: one half-court heat map of the change in shot share since the late 1990s."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ...bundle import Axis, Encoding, Grid
from ...sources import nba
from ..registry import ChartSpec, Context, chart

# Shots inside 4 ft of the rim are left out: the 1990s feed logs most of them at the basket itself
# (23% of all shots sit at exactly (0, 0) then, 3% now), which would swamp a change map.
EARLY = (1998, 2001)  # 1997-98 to 2000-01: the first four seasons after the line went back to 23'9"
LATE_SEASONS = 3  # the most recent three seasons in the cache, the current one included
BIN_WIDTH = 20.0  # hexagon flat-to-flat width in tenths of a foot (2 ft)
MIN_SHARE = 0.0002  # drop hexes that hold under 0.02% of shots in both eras (noise, bundle size)

# NBA.com shot coordinates: basket at the origin, tenths of a foot, baseline 5.25 ft behind the rim
X_RANGE = (-250.0, 250.0)
Y_RANGE = (-52.5, 417.5)

POINTS_SQL = """
SELECT era, x_legacy AS x, y_legacy AS y, count(*) AS n
FROM (
    SELECT CASE WHEN season BETWEEN ? AND ? THEN 'early' WHEN season >= ? THEN 'late' END AS era,
           x_legacy, y_legacy
    FROM shots
    WHERE season_type_id = ? AND x_legacy IS NOT NULL AND y_legacy IS NOT NULL
      AND x_legacy * x_legacy + y_legacy * y_legacy > 1600  -- outside 4 ft of the rim
) t
WHERE era IS NOT NULL
GROUP BY era, x_legacy, y_legacy
"""

ZONES_SQL = """
SELECT CASE WHEN season BETWEEN ? AND ? THEN 'early' WHEN season >= ? THEN 'late' END AS era,
       avg(CASE WHEN shot_value = 3 THEN 1.0 ELSE 0.0 END) AS three,
       avg(CASE WHEN shot_value = 2 AND shot_distance >= 10 THEN 1.0 ELSE 0.0 END) AS midrange,
       count(*) AS n
FROM shots
WHERE season_type_id = ?
GROUP BY era
HAVING era IS NOT NULL
"""


def hex_centers(x: np.ndarray, y: np.ndarray, width: float) -> tuple[np.ndarray, np.ndarray]:
    """Snap points to the centres of a pointy-top hexagonal grid of the given flat-to-flat width."""
    size = width / np.sqrt(3)  # centre to vertex
    q = (np.sqrt(3) / 3 * x - y / 3) / size
    r = (2 / 3 * y) / size
    s = -q - r
    rq, rr, rs = np.round(q), np.round(r), np.round(s)
    dq, dr, ds = np.abs(rq - q), np.abs(rr - r), np.abs(rs - s)
    fix_q = (dq > dr) & (dq > ds)
    fix_r = ~fix_q & (dr > ds)
    rq = np.where(fix_q, -rr - rs, rq)
    rr = np.where(fix_r, -rq - rs, rr)
    return size * np.sqrt(3) * (rq + rr / 2), size * 1.5 * rr


@chart(
    ChartSpec(
        league="nba",
        slug="shot-chart-shift",
        kind="heatmap",
        title="Where the midrange went",
        subtitle=(
            "Change in the share of all shots taken from each spot on the floor: the last three seasons "
            "against 1997-98 to 2000-01. Regular season, shots inside 4 ft of the rim left out, "
            "hexagons two feet wide"
        ),
        source=nba.SOURCE,
        tags=("heatmap", "shot-chart", "midrange", "three-point"),
    )
)
def compute(ctx: Context) -> dict:
    seasons = [
        int(s) for (s,) in ctx.con.execute("SELECT DISTINCT season FROM shots ORDER BY season").fetchall()
    ]
    late_from = sorted(seasons)[-LATE_SEASONS]
    params = [EARLY[0], EARLY[1], late_from, nba.REGULAR_SEASON]
    pts = ctx.con.execute(POINTS_SQL, params).df()
    zones = ctx.con.execute(ZONES_SQL, params).df().set_index("era")

    cx, cy = hex_centers(pts["x"].to_numpy(float), pts["y"].to_numpy(float), BIN_WIDTH)
    binned = (
        pd.DataFrame({"era": pts["era"], "cx": np.round(cx, 1), "cy": np.round(cy, 1), "n": pts["n"]})
        .groupby(["era", "cx", "cy"], as_index=False)["n"]
        .sum()
    )
    totals = binned.groupby("era")["n"].sum()
    binned["share"] = binned["n"] / binned["era"].map(totals)
    wide = binned.pivot_table(index=["cx", "cy"], columns="era", values=["n", "share"], fill_value=0.0)
    n_all = wide["n"].sum(axis=1)
    early_share = wide["share"].get("early", 0.0)
    late_share = wide["share"].get("late", 0.0)
    keep = (
        ((early_share >= MIN_SHARE) | (late_share >= MIN_SHARE))
        & wide.index.get_level_values("cx").to_series(index=wide.index).between(*X_RANGE)
        & wide.index.get_level_values("cy").to_series(index=wide.index).between(*Y_RANGE)
    )
    delta_pp = (late_share - early_share) * 100
    cells = [
        [float(cx_), float(cy_), int(n_all[idx]), round(float(delta_pp[idx]), 3)]
        for idx, (cx_, cy_) in zip(wide.index[keep], wide.index[keep], strict=True)
    ]

    e, late = zones.loc["early"], zones.loc["late"]
    early_label = f"{nba.season_label(EARLY[0])} to {nba.season_label(EARLY[1])}"
    late_label = f"{nba.season_label(late_from)} to {nba.season_label(max(seasons))}"
    hook = (
        f"From {early_label}, {e.midrange:.0%} of NBA shots were midrange twos and {e.three:.0%} were "
        f"threes. From {late_label}: {late.midrange:.0%} midrange, {late.three:.0%} threes."
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="x", label="Court position"),
            y=Axis(field="value", label="Change in share of all shots (percentage points)", format="+.2f"),
        ),
        grid=Grid(
            shape="hex",
            bin_width=BIN_WIDTH,
            x_range=list(X_RANGE),
            y_range=list(Y_RANGE),
            court="nba_halfcourt",
            value_label="pp",
            cells=cells,
        ),
        summary={
            "early": {
                "seasons": early_label,
                "midrange": round(float(e.midrange), 4),
                "three": round(float(e.three), 4),
            },
            "late": {
                "seasons": late_label,
                "midrange": round(float(late.midrange), 4),
                "three": round(float(late.three), 4),
            },
        },
        data_through=nba.data_through(ctx.extras.get("stamp_path")),
    )
