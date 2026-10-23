"""The kickoff return, killed by rule changes and brought back by the 2024 dynamic kickoff."""

from __future__ import annotations

from ...bundle import Annotation, Axis, Domain, Encoding, Series, Table
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

SQL = """
SELECT season,
       count(*) AS kickoffs,
       avg(CASE WHEN coalesce(touchback, 0) = 1 THEN 1.0 ELSE 0.0 END) AS touchback,
       avg(CASE WHEN coalesce(kickoff_fair_catch, 0) = 1 THEN 1.0 ELSE 0.0 END) AS fair_catch,
       avg(CASE WHEN coalesce(touchback, 0) = 0 AND coalesce(kickoff_fair_catch, 0) = 0
                 AND coalesce(kickoff_out_of_bounds, 0) = 0 AND coalesce(kickoff_downed, 0) = 0
                 AND coalesce(own_kickoff_recovery, 0) = 0 THEN 1.0 ELSE 0.0 END) AS returned
FROM pbp
WHERE season_type = 'REG' AND play_type = 'kickoff'
GROUP BY season
ORDER BY season
"""

SERIES = [
    Series(key="returned", label="Returned", emphasis=True),
    Series(key="touchback", label="Touchback"),
    Series(key="fair_catch", label="Fair catch"),
]

ANNOTATIONS = [
    Annotation(kind="vline", x=2011, label="Kickoff moved up to the 35"),
    Annotation(kind="vline", x=2016, label="Touchback out to the 25"),
    Annotation(kind="vline", x=2018, label="No running start"),
    Annotation(kind="vline", x=2023, label="Fair catch = ball at the 25"),
    Annotation(kind="vline", x=2024, label="Dynamic kickoff"),
    Annotation(kind="vline", x=2025, label="Touchback out to the 35"),
]


@chart(
    ChartSpec(
        league="nfl",
        slug="kickoff-return-rate",
        kind="line",
        title="The kickoff return is back",
        subtitle="What happens on a regular-season kickoff, 1999 to today",
        source=nfl.SOURCE,
        tags=("trend", "special-teams", "rule-change"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL).df()
    long = df.melt(
        id_vars=["season"], value_vars=[s.key for s in SERIES], var_name="series", value_name="value"
    ).dropna()
    rows = [[int(r.season), str(r.series), round(float(r.value), 4)] for r in long.itertuples(index=False)]

    ret = df.set_index("season")["returned"]
    first_s, last_s = int(ret.index.min()), int(ret.index.max())
    low_s = int(ret.idxmin())
    hook = (
        f"In {first_s}, {ret.iloc[0]:.0%} of kickoffs were returned. By {low_s} it was {ret.min():.0%}. "
        f"In {last_s}: {ret.iloc[-1]:.0%}."
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="season", label="Season", format="d"),
            y=Axis(field="value", label="Share of kickoffs", format=".0%"),
            series=Axis(field="series", type="nominal", label="Outcome"),
        ),
        domain=Domain(x=[first_s, last_s], y=[0, 1]),
        series=SERIES,
        annotations=ANNOTATIONS
        + [Annotation(kind="point", x=low_s, y=round(float(ret.min()), 4), label="Low")],
        data=Table(columns=["season", "series", "value"], rows=rows),
        data_through=nfl.data_through(ctx.con),
    )
