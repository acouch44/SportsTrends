"""The analytics revolution on 4th-and-short, zone by zone."""

from __future__ import annotations

import pandas as pd

from ...bundle import Annotation, Axis, Domain, Encoding, Facet, Series, Table
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

SQL = """
WITH f AS (
    SELECT season,
           play_type,
           CASE WHEN yardline_100 <= 20 THEN 'red_zone'
                WHEN yardline_100 <= 40 THEN 'opp_21_40'
                WHEN yardline_100 <= 60 THEN 'midfield'
                ELSE 'own_side' END AS zone
    FROM pbp
    WHERE season_type = 'REG' AND down = 4 AND ydstogo <= 2 AND qtr <= 3
      AND abs(score_differential) <= 8
      AND play_type IN ('pass', 'run', 'punt', 'field_goal')
)
SELECT season, zone,
       avg(CASE WHEN play_type IN ('pass', 'run') THEN 1.0 ELSE 0.0 END) AS go_rate,
       count(*) AS n
FROM f
GROUP BY season, zone
ORDER BY season, zone
"""

FACETS = [
    Facet(key="all", label="All field positions"),
    Facet(key="own_side", label="Own side of midfield"),
    Facet(key="midfield", label="Midfield to the opponent 41"),
    Facet(key="opp_21_40", label="Opponent 21 to 40"),
    Facet(key="red_zone", label="Opponent 20 and in"),
]


@chart(
    ChartSpec(
        league="nfl",
        slug="fourth-down-go-rate",
        kind="small_multiples",
        title="Going for it on 4th-and-short",
        subtitle=(
            "Share of 4th-and-1 or 2 plays where the offense went for it instead of kicking. "
            "Quarters 1-3, score within one possession, regular season"
        ),
        source=nfl.SOURCE,
        tags=("trend", "analytics", "fourth-down"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL).df()
    df["went"] = df["go_rate"] * df["n"]
    allz = df.groupby("season", as_index=False)[["went", "n"]].sum()
    allz["go_rate"] = allz["went"] / allz["n"]
    allz["zone"] = "all"
    full = pd.concat([allz[["season", "zone", "go_rate", "n"]], df[["season", "zone", "go_rate", "n"]]])
    full = full.sort_values(["zone", "season"])
    rows = [
        [int(r.season), str(r.zone), "go_rate", round(float(r.go_rate), 4), int(r.n)]
        for r in full.itertuples(index=False)
    ]

    a = allz.set_index("season")["go_rate"]
    first_s, last_s = int(a.index.min()), int(a.index.max())
    hook = (
        f"On 4th-and-short with the game close, teams went for it {a.iloc[0]:.0%} of the time in {first_s}. "
        f"In {last_s}: {a.iloc[-1]:.0%}."
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="season", label="Season", format="d"),
            y=Axis(field="value", label="Go-for-it rate", format=".0%"),
            series=Axis(field="series", type="nominal"),
            facet=Axis(field="facet", type="nominal", label="Field position"),
        ),
        domain=Domain(x=[first_s, last_s], y=[0, 1]),
        series=[Series(key="go_rate", label="Went for it", emphasis=True)],
        facets=FACETS,
        annotations=[Annotation(kind="vline", x=2018, label="4th-down analytics goes mainstream")],
        data=Table(columns=["season", "facet", "series", "value", "n"], rows=rows),
        data_through=nfl.data_through(ctx.con),
    )
