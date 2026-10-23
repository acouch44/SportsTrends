"""The wildest game of the most recent completed week, as a win-probability line.

"Wildest" is the game with the largest total win-probability movement (the sum of |WPA| over its
plays, the usual game excitement index). Refreshes automatically as each week completes.
"""

from __future__ import annotations

from ...bundle import Axis, Domain, Encoding, KeyPlay, Series, Story, Table
from ...sources import nfl
from ..registry import ChartSpec, Context, chart

PICK_SQL = """
SELECT game_id, sum(abs(coalesce(vegas_wpa, wpa))) AS excitement
FROM pbp
WHERE season = ? AND week = ? AND season_type = 'REG' AND coalesce(vegas_wpa, wpa) IS NOT NULL
GROUP BY game_id
ORDER BY excitement DESC
LIMIT 1
"""

GAME_SQL = """
SELECT play_id, qtr, quarter_seconds_remaining AS qsr, time, "desc",
       coalesce(vegas_home_wp, home_wp) AS wp,
       total_home_score, total_away_score, home_team, away_team, game_date, week, season
FROM pbp
WHERE game_id = ? AND coalesce(vegas_home_wp, home_wp) IS NOT NULL
ORDER BY qtr, quarter_seconds_remaining DESC, play_id
"""


def _season_and_week(ctx: Context) -> tuple[int, int]:
    con = ctx.con
    season = con.execute("SELECT max(season) FROM pbp WHERE season_type = 'REG'").fetchone()[0]
    season = int(season)
    week = None
    if nfl.has_view(con, "schedules"):
        row = con.execute(
            """
            SELECT max(week) FROM (
                SELECT week FROM schedules
                WHERE season = ? AND game_type = 'REG'
                GROUP BY week HAVING count(*) = count(result) AND count(result) > 0
            )
            """,
            [season],
        ).fetchone()
        week = row[0] if row else None
    if week is None:
        week = con.execute(
            "SELECT max(week) FROM pbp WHERE season = ? AND season_type = 'REG'", [season]
        ).fetchone()[0]
    return season, int(week)


@chart(
    ChartSpec(
        league="nfl",
        slug="wp-rollercoaster",
        kind="wp_story",
        title="Win-probability rollercoaster of the week",
        source=nfl.SOURCE,
        tags=("game", "win-probability", "weekly"),
    )
)
def compute(ctx: Context) -> dict:
    con = ctx.con
    season, week = _season_and_week(ctx)
    pick = con.execute(PICK_SQL, [season, week]).fetchone()
    if pick is None:
        raise RuntimeError(f"no plays with win probability for {season} week {week}")
    game_id, excitement = pick
    g = con.execute(GAME_SQL, [game_id]).df()
    if g.empty:
        raise RuntimeError(f"game {game_id} has no win-probability rows")

    ot_len = float(g.loc[g["qtr"] >= 5, "qsr"].max()) if (g["qtr"] >= 5).any() else 600.0
    reg = g["qtr"] <= 4
    g["elapsed"] = 0.0
    g.loc[reg, "elapsed"] = (g.loc[reg, "qtr"] - 1) * 900 + (900 - g.loc[reg, "qsr"])
    g.loc[~reg, "elapsed"] = 3600 + (g.loc[~reg, "qtr"] - 5) * ot_len + (ot_len - g.loc[~reg, "qsr"])
    g["wp"] = g["wp"].astype(float).clip(0, 1)
    g["dwp"] = g["wp"].diff().fillna(0.0)

    home, away = str(g["home_team"].iloc[0]), str(g["away_team"].iloc[0])
    colors = nfl.team_colors(con)
    hc, ac = colors.get(home, {}), colors.get(away, {})
    last = g.iloc[-1]
    final = f"{away} {int(last.total_away_score)} - {home} {int(last.total_home_score)}"
    date = str(last.game_date)[:10]

    key_plays = []
    for r in g.reindex(g["dwp"].abs().sort_values(ascending=False).index).head(3).itertuples(index=False):
        key_plays.append(
            KeyPlay(
                elapsed=round(float(r.elapsed), 1),
                qtr=int(r.qtr),
                clock=str(r.time or ""),
                wp_before=round(float(r.wp - r.dwp), 4),
                wp_after=round(float(r.wp), 4),
                desc=str(r.desc or "")[:220],
                score=f"{away} {int(r.total_away_score)} - {home} {int(r.total_home_score)}",
            )
        )
    key_plays.sort(key=lambda k: k.elapsed)

    rows = [
        [round(float(r.elapsed), 1), round(float(r.wp), 4), int(r.qtr)] for r in g.itertuples(index=False)
    ]
    # the last row is the final whistle (0% or 100% by definition); the story is what came before
    core = g.iloc[:-1] if len(g) > 1 else g
    peak_i, trough_i = core["wp"].idxmax(), core["wp"].idxmin()
    peak, peak_q = float(core.at[peak_i, "wp"]), int(core.at[peak_i, "qtr"])
    trough, trough_q = float(core.at[trough_i, "wp"]), int(core.at[trough_i, "qtr"])
    home_won = int(last.total_home_score) > int(last.total_away_score)
    story = Story(
        game_id=str(game_id),
        season=season,
        week=week,
        date=date,
        home=home,
        away=away,
        home_name=hc.get("name", home),
        away_name=ac.get("name", away),
        home_color=hc.get("color", "#444444"),
        away_color=ac.get("color", "#999999"),
        final=final,
        excitement=round(float(excitement), 3),
        key_plays=key_plays,
    )

    def _q(q: int) -> str:
        return f"the {['first', 'second', 'third', 'fourth'][q - 1]} quarter" if q <= 4 else "overtime"

    if home_won:
        hook = (
            f"Week {week}: {story.home_name} were down to a {trough:.0%} chance of winning in {_q(trough_q)} "
            f"and won anyway. Final {final}."
        )
    else:
        hook = (
            f"Week {week}: {story.home_name} had a {peak:.0%} chance of winning in {_q(peak_q)} "
            f"and lost. Final {final}."
        )
    return dict(
        subtitle=f"Week {week}, {season}: {story.away_name} at {story.home_name} ({date}). Final {final}.",
        hook=hook,
        encoding=Encoding(
            x=Axis(field="elapsed", label="Game time", format="elapsed"),
            y=Axis(field="wp", label=f"{home} win probability", format=".0%"),
        ),
        domain=Domain(x=[0, float(g["elapsed"].max())], y=[0, 1]),
        series=[Series(key="wp", label=f"{home} win probability", color=story.home_color, emphasis=True)],
        data=Table(columns=["elapsed", "wp", "qtr"], rows=rows),
        story=story,
        data_through=date,
    )
