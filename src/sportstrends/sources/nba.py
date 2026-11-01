"""NBA: stats.nba.com shot locations via the sportsdataverse mirror (1996-97 on).

One parquet per season, labelled by the season's ending year (1997 = 1996-97). Each row is a field
goal attempt: who, which team, made or missed, 2 or 3, distance, and the court position in tenths
of a foot with the basket at the origin (``x_legacy`` -250..250, ``y_legacy`` up the floor).
``season_type_id`` is '2' for the regular season, '4' playoffs, '5' play-in, '6' the Cup final.
Team colours and full player names (the feed carries surnames only) are vendored JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from ..config import RAW, VENDOR_DIR
from ..config import current_season as _current
from .releases import SDV, Asset

FIRST_SEASON = 1997
SHOTS = Asset("nba", "shots", f"{SDV}/nba_stats_shots/shots_{{season}}.parquet", FIRST_SEASON)
STAMP = Asset("nba", "shots_stamp", f"{SDV}/nba_stats_shots/timestamp.txt")  # mirror's last refresh
TEAMS_PATH = VENDOR_DIR / "nba" / "teams.json"
PLAYERS_PATH = VENDOR_DIR / "nba" / "players.json"
REGULAR_SEASON = "2"

SOURCE = {
    "name": "sportsdataverse",
    "url": "https://github.com/sportsdataverse/sportsdataverse-data",
    "license": "MIT (mirror of NBA.com stats)",
    "attribution": "Data: NBA.com shot charts via sportsdataverse",
}

# tricodes used in older seasons for franchises that have since moved or been renamed
TEAM_ALIASES = {
    "SEA": "OKC",
    "NJN": "BKN",
    "NOH": "NOP",
    "NOK": "NOP",
    "VAN": "MEM",
    "CHH": "CHA",
    "WSB": "WAS",
}


def seasons(current: int | None = None) -> list[int]:
    return list(range(FIRST_SEASON, (current or _current("nba")) + 1))


def fetch(*, current_only: bool = False, force: bool = False) -> list[Path]:
    cur = _current("nba")
    wanted = [cur] if current_only else seasons(cur)
    paths = [p for s in wanted if (p := SHOTS.download(s, current_season=cur, force=force))]
    if p := STAMP.download(force=force):
        paths.append(p)
    return paths


def connect(shots_glob: str | None = None) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with a ``shots`` view over whatever seasons are cached."""
    con = duckdb.connect()
    shots_glob = shots_glob or (RAW / "nba" / "shots_*.parquet").as_posix()
    con.execute(f"CREATE VIEW shots AS SELECT * FROM read_parquet('{shots_glob}', union_by_name=true)")
    return con


def data_through(stamp_path: Path | None = None) -> str:
    """ISO date of the mirror's last refresh (the shot feed carries no game dates)."""
    p = Path(stamp_path or STAMP.path())
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()[:10]


def team_colors(path: Path | None = None) -> dict[str, dict[str, str]]:
    """tricode -> {name, color, color2}, with old tricodes pointing at the current franchise."""
    p = Path(path or TEAMS_PATH)
    if not p.exists():
        return {}
    out: dict[str, dict[str, str]] = json.loads(p.read_text(encoding="utf-8"))
    for old, new in TEAM_ALIASES.items():
        if new in out and old not in out:
            out[old] = out[new]
    return out


def player_names(path: Path | None = None) -> dict[int, str]:
    """person_id -> full name for the players who matter to a chart; surnames stand in otherwise."""
    p = Path(path or PLAYERS_PATH)
    if not p.exists():
        return {}
    return {int(k): v for k, v in json.loads(p.read_text(encoding="utf-8")).items()}


def season_label(season: int) -> str:
    """1997 -> '1996-97'."""
    return f"{season - 1}-{season % 100:02d}"
