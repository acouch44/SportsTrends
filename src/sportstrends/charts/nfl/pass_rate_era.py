"""Run vs. pass: the NFL dropback rate by season, league-wide and in neutral situations."""

from __future__ import annotations

from ...bundle import Annotation, Axis, Domain, Encoding, Series, Table
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

SQL = """
SELECT season,
       avg("pass")::DOUBLE AS all_plays,
       avg(CASE WHEN wp BETWEEN 0.2 AND 0.8 AND qtr <= 3 THEN "pass" END)::DOUBLE AS neutral,
       avg(CASE WHEN wp BETWEEN 0.2 AND 0.8 AND qtr <= 3 AND down IN (1, 2) THEN "pass" END)::DOUBLE
           AS early_neutral,
       count(*) AS plays
FROM pbp
WHERE season_type = 'REG' AND ("pass" = 1 OR rush = 1) AND play_type <> 'no_play'
GROUP BY season
ORDER BY season
"""

SERIES = [
    Series(key="early_neutral", label="Early downs, game in doubt", emphasis=True),
    Series(key="neutral", label="All downs, game in doubt"),
    Series(key="all_plays", label="Every offensive play"),
]

ANNOTATIONS = [
    Annotation(kind="vline", x=2004, label="Illegal-contact crackdown"),
    Annotation(kind="vline", x=2011, label="New CBA limits contact practice"),
    Annotation(kind="vline", x=2018, label="Helmet & roughing rules; scoring peaks"),
]


@chart(
    ChartSpec(
        league="nfl",
        slug="pass-rate-era",
        kind="line",
        title="Run vs. pass: how often the NFL drops back",
        subtitle="Share of offensive plays that were dropbacks (passes, sacks, scrambles), regular season",
        source=nfl.SOURCE,
        tags=("trend", "offense", "run-vs-pass"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL).df()
    long = df.melt(
        id_vars=["season"], value_vars=[s.key for s in SERIES], var_name="series", value_name="value"
    ).dropna()
    rows = [[int(r.season), str(r.series), round(float(r.value), 4)] for r in long.itertuples(index=False)]

    en = df.set_index("season")["early_neutral"].dropna()
    first_s, last_s = int(en.index.min()), int(en.index.max())
    peak_s = int(en.idxmax())
    hook = (
        f"On early downs with the game in doubt, offenses dropped back {en.iloc[0]:.0%} of the time in "
        f"{first_s}. In {last_s} it is {en.iloc[-1]:.0%}; the peak was {en.max():.0%} in {peak_s}."
    )
    lo = min(0.4, float(long["value"].min()) - 0.02)
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="season", label="Season", format="d"),
            y=Axis(field="value", label="Dropback rate", format=".0%"),
            series=Axis(field="series", type="nominal", label="Situation"),
        ),
        domain=Domain(x=[first_s, last_s], y=[round(lo, 2), 0.7]),
        series=SERIES,
        annotations=ANNOTATIONS
        + [Annotation(kind="point", x=peak_s, y=round(float(en.max()), 4), label="Peak")],
        data=Table(columns=["season", "series", "value"], rows=rows),
        data_through=nfl.data_through(ctx.con),
    )
