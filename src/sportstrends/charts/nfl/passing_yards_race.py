"""Cumulative regular-season passing yards since 1999 as a bar-chart race, one frame per season."""

from __future__ import annotations

from ...bundle import Axis, Encoding, Frame, RankItem
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

SQL = """
SELECT season,
       passer_player_id AS pid,
       any_value(passer_player_name) AS name,
       mode(posteam) AS team,
       sum(passing_yards) AS yds
FROM pbp
WHERE season_type = 'REG' AND passer_player_id IS NOT NULL AND passing_yards IS NOT NULL
GROUP BY season, passer_player_id
"""

TOP_N = 12


@chart(
    ChartSpec(
        league="nfl",
        slug="passing-yards-race",
        kind="race",
        title="The passing-yards race, 1999 to today",
        subtitle=f"Cumulative regular-season passing yards since 1999, top {TOP_N} after each season",
        source=nfl.SOURCE,
        tags=("race", "quarterbacks", "records"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL).df()
    df = df.dropna(subset=["pid"])
    cum = df.pivot_table(index="season", columns="pid", values="yds", aggfunc="sum").fillna(0.0).cumsum()
    teams = df.pivot_table(index="season", columns="pid", values="team", aggfunc="first").ffill()
    names = df.sort_values("season").groupby("pid")["name"].last()
    colors = nfl.team_colors(ctx.con)

    frames: list[Frame] = []
    for season in cum.index:
        top = cum.loc[season].nlargest(TOP_N)
        ranks = []
        for pid, yds in top.items():
            if yds <= 0:
                continue
            team = teams.at[season, pid] if pid in teams.columns else None
            team = str(team) if isinstance(team, str) else None
            ranks.append(
                RankItem(
                    key=str(pid),
                    label=str(names.get(pid, pid)),
                    value=float(round(yds)),
                    color=colors.get(team or "", {}).get("color"),
                    group=team,
                )
            )
        frames.append(Frame(t=str(int(season)), ranks=ranks))

    leader = frames[-1].ranks[0] if frames and frames[-1].ranks else None
    hook = (
        f"{leader.label} leads everyone who has thrown a pass since 1999 with {leader.value:,.0f} yards "
        f"(through {frames[-1].t})."
        if leader
        else ""
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="value", label="Passing yards since 1999", format=",.0f"),
            y=Axis(field="label", type="nominal", label="Quarterback"),
        ),
        frames=frames,
        data_through=nfl.data_through(ctx.con),
    )
