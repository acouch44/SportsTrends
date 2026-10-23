"""NFL: nflverse play-by-play (1999-), schedules and team colours."""

from __future__ import annotations

from pathlib import Path

import duckdb

from ..config import RAW
from ..config import current_season as _current
from .releases import NFLVERSE, Asset

FIRST_SEASON = 1999
PBP = Asset("nfl", "pbp", f"{NFLVERSE}/pbp/play_by_play_{{season}}.parquet", FIRST_SEASON)
SCHEDULES = Asset("nfl", "schedules", f"{NFLVERSE}/schedules/games.parquet")
TEAMS = Asset("nfl", "teams", f"{NFLVERSE}/teams/teams_colors_logos.parquet")

SOURCE = {
    "name": "nflverse",
    "url": "https://github.com/nflverse/nflverse-data",
    "license": "CC-BY-4.0",
    "attribution": "Data: nflverse (nflfastR play-by-play)",
}

# abbreviations used in older play-by-play for franchises that have since moved
TEAM_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LA"}


def seasons(current: int | None = None) -> list[int]:
    return list(range(FIRST_SEASON, (current or _current("nfl")) + 1))


def fetch(*, current_only: bool = False, force: bool = False) -> list[Path]:
    cur = _current("nfl")
    wanted = [cur] if current_only else seasons(cur)
    paths = [p for s in wanted if (p := PBP.download(s, current_season=cur, force=force))]
    for asset in (SCHEDULES, TEAMS):
        if p := asset.download(force=force):
            paths.append(p)
    return paths


def connect(
    pbp_glob: str | None = None, teams_path: Path | None = None, schedules_path: Path | None = None
) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with ``pbp``, ``teams`` and ``schedules`` views over whatever is cached."""
    con = duckdb.connect()
    pbp_glob = pbp_glob or (RAW / "nfl" / "pbp_*.parquet").as_posix()
    con.execute(f"CREATE VIEW pbp AS SELECT * FROM read_parquet('{pbp_glob}', union_by_name=true)")
    teams_path = Path(teams_path or TEAMS.path())
    if teams_path.exists():
        con.execute(f"CREATE VIEW teams AS SELECT * FROM read_parquet('{teams_path.as_posix()}')")
    schedules_path = Path(schedules_path or SCHEDULES.path())
    if schedules_path.exists():
        con.execute(f"CREATE VIEW schedules AS SELECT * FROM read_parquet('{schedules_path.as_posix()}')")
    return con


def has_view(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = con.execute("SELECT count(*) FROM duckdb_views() WHERE view_name = ?", [name]).fetchone()
    return bool(row and row[0])


def data_through(con: duckdb.DuckDBPyConnection) -> str:
    """ISO date of the last game present in the play-by-play."""
    row = con.execute("SELECT max(game_date) FROM pbp").fetchone()
    return str(row[0])[:10] if row and row[0] else ""


def team_colors(con: duckdb.DuckDBPyConnection) -> dict[str, dict[str, str]]:
    """abbr -> {name, color, color2}; empty when the teams file is not cached."""
    if not has_view(con, "teams"):
        return {}
    rows = con.execute("SELECT team_abbr, team_name, team_color, team_color2 FROM teams").fetchall()
    out = {
        abbr: {"name": name, "color": c1 or "#444444", "color2": c2 or "#999999"}
        for abbr, name, c1, c2 in rows
    }
    for old, new in TEAM_ALIASES.items():
        if new in out and old not in out:
            out[old] = out[new]
    return out
