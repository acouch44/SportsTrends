"""Share of NBA field-goal attempts taken from three, season by season since 1996-97."""

from __future__ import annotations

from ...bundle import Annotation, Axis, Domain, Encoding, Series, Table
from ...sources import nba
from ..registry import ChartSpec, Context, chart

SQL = """
SELECT season,
       avg(CASE WHEN shot_value = 3 THEN 1.0 ELSE 0.0 END) AS rate,
       count(*) AS n
FROM shots
WHERE season_type_id = ?
GROUP BY season
ORDER BY season
"""


@chart(
    ChartSpec(
        league="nba",
        slug="three-point-rate",
        kind="line",
        title="The three-point takeover",
        subtitle="Share of all NBA field-goal attempts taken from behind the arc, regular season",
        source=nba.SOURCE,
        tags=("trend", "three-point", "shooting"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL, [nba.REGULAR_SEASON]).df().sort_values("season")
    rows = [[int(r.season), round(float(r.rate), 4), int(r.n)] for r in df.itertuples(index=False)]
    first, last = df.iloc[0], df.iloc[-1]
    peak = df.loc[df["rate"].idxmax()]
    first_s, last_s = int(first.season), int(last.season)
    # the hook starts the story in 1997-98, the first season back at 23'9" after three short-line years
    base = df[df["season"] == 1998].iloc[0] if (df["season"] == 1998).any() else first
    hook = (
        f"In {nba.season_label(int(base.season))}, {base.rate:.0%} of NBA shots were threes, "
        f"about 1 in {round(1 / base.rate)}. In {nba.season_label(last_s)}: {last.rate:.0%}, "
        f"about {round(10 * last.rate)} in 10."
    )
    annotations = [
        Annotation(kind="vline", x=1998, label="Line moved back to 23 ft 9 in"),
        Annotation(kind="vline", x=2015, label="Warriors' first title"),
    ]
    if int(peak.season) != last_s:
        annotations.append(
            Annotation(kind="point", x=int(peak.season), y=round(float(peak.rate), 4), label="Peak")
        )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="season", label="Season (year it ends)", format="d"),
            y=Axis(field="value", label="Share of shots from three", format=".0%"),
        ),
        domain=Domain(x=[first_s, last_s], y=[0, 0.5]),
        series=[Series(key="value", label="Share of shots from three", emphasis=True)],
        annotations=annotations,
        data=Table(columns=["season", "value", "n"], rows=rows),
        data_through=nba.data_through(ctx.extras.get("stamp_path")),
    )
