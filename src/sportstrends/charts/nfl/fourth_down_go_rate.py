"""The analytics revolution on 4th-and-short: one line for the league, one for its boldest form."""

from __future__ import annotations

from ...bundle import Annotation, Axis, Domain, Encoding, Series, Table
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

# 4th-and-1 or 2, quarters 1-3, score within one possession, regular season. "Went for it" means a
# pass or run instead of a punt or field goal. Own side of midfield = more than 50 yards to the goal.
SQL = """
WITH f AS (
    SELECT season,
           play_type IN ('pass', 'run') AS went,
           yardline_100 > 50 AS own_side
    FROM pbp
    WHERE season_type = 'REG' AND down = 4 AND ydstogo <= 2 AND qtr <= 3
      AND abs(score_differential) <= 8
      AND play_type IN ('pass', 'run', 'punt', 'field_goal')
)
SELECT season,
       avg(CASE WHEN went THEN 1.0 ELSE 0.0 END) AS all_rate,
       count(*) AS all_n,
       avg(CASE WHEN own_side THEN CASE WHEN went THEN 1.0 ELSE 0.0 END END) AS own_rate,
       sum(CASE WHEN own_side THEN 1 ELSE 0 END) AS own_n
FROM f
GROUP BY season
ORDER BY season
"""


@chart(
    ChartSpec(
        league="nfl",
        slug="fourth-down-go-rate",
        kind="line",
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
    df = ctx.con.execute(SQL).df().sort_values("season")
    rows: list[list] = []
    for r in df.itertuples(index=False):
        rows.append([int(r.season), "all", round(float(r.all_rate), 4), int(r.all_n)])
        if r.own_n:
            rows.append([int(r.season), "own_side", round(float(r.own_rate), 4), int(r.own_n)])

    first, last = df.iloc[0], df.iloc[-1]
    first_s, last_s = int(first.season), int(last.season)
    hook = (
        f"In {first_s}, teams went for it on close-game 4th-and-short {first.all_rate:.0%} of the time. "
        f"In {last_s}: {last.all_rate:.0%}. On their own side of midfield it went from "
        f"{first.own_rate:.0%} to {last.own_rate:.0%}."
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="season", label="Season", format="d"),
            y=Axis(field="value", label="Go-for-it rate", format=".0%"),
            series=Axis(field="series", type="nominal"),
        ),
        domain=Domain(x=[first_s, last_s], y=[0, 0.8]),
        series=[
            Series(key="all", label="Anywhere on the field", emphasis=True),
            Series(key="own_side", label="Own side of midfield"),
        ],
        annotations=[Annotation(kind="vline", x=2018, label="4th-down analytics goes mainstream")],
        data=Table(columns=["season", "series", "value", "n"], rows=rows),
        data_through=nfl.data_through(ctx.con),
    )
