"""Cumulative regular-season three-pointers made since 1996-97 as a bar-chart race, one frame per season."""

from __future__ import annotations

from ...bundle import Axis, Encoding, Frame, RankItem
from ...sources import nba
from ..registry import ChartSpec, Context, chart

SQL = """
SELECT season,
       person_id AS pid,
       any_value(player_name) AS surname,
       mode(team_tricode) AS team,
       count(*) AS made
FROM shots
WHERE season_type_id = ? AND shot_value = 3 AND shot_result = 'Made' AND person_id IS NOT NULL
GROUP BY season, person_id
"""

TOP_N = 12


@chart(
    ChartSpec(
        league="nba",
        slug="three-pointers-race",
        kind="race",
        title="The three-point race, 1996-97 to today",
        subtitle=f"Cumulative regular-season threes made since 1996-97, top {TOP_N} after each season",
        source=nba.SOURCE,
        tags=("race", "three-point", "records"),
    )
)
def compute(ctx: Context) -> dict:
    df = ctx.con.execute(SQL, [nba.REGULAR_SEASON]).df()
    cum = df.pivot_table(index="season", columns="pid", values="made", aggfunc="sum").fillna(0.0).cumsum()
    teams = df.pivot_table(index="season", columns="pid", values="team", aggfunc="first").ffill()
    surnames = df.sort_values("season").groupby("pid")["surname"].last()
    names = nba.player_names(ctx.extras.get("players_path"))
    colors = nba.team_colors(ctx.extras.get("teams_path"))

    frames: list[Frame] = []
    for season in cum.index:
        top = cum.loc[season].nlargest(TOP_N)
        ranks = []
        for pid, made in top.items():
            if made <= 0:
                continue
            team = teams.at[season, pid] if pid in teams.columns else None
            team = str(team) if isinstance(team, str) else None
            ranks.append(
                RankItem(
                    key=str(int(pid)),
                    label=names.get(int(pid)) or str(surnames.get(pid, pid)),
                    value=float(made),
                    color=colors.get(team or "", {}).get("color"),
                    group=team,
                )
            )
        frames.append(Frame(t=nba.season_label(int(season)), ranks=ranks))

    leader = frames[-1].ranks[0] if frames and frames[-1].ranks else None
    hook = (
        f"{leader.label} has made {leader.value:,.0f} regular-season threes since 1996-97, more than anyone "
        f"else over that span (through {frames[-1].t})."
        if leader
        else ""
    )
    return dict(
        hook=hook,
        encoding=Encoding(
            x=Axis(field="value", label="Threes made since 1996-97", format=",.0f"),
            y=Axis(field="label", type="nominal", label="Player"),
        ),
        frames=frames,
        data_through=nba.data_through(ctx.extras.get("stamp_path")),
    )
