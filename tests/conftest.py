"""Tiny synthetic feeds shaped like the real ones so every chart can be computed offline in tests."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from sportstrends.charts import registry
from sportstrends.sources import nba, nfl

TEAMS = ["KC", "BUF", "DET", "SF"]
QBS = {
    "KC": ("00-0033873", "P.Mahomes"),
    "BUF": ("00-0034857", "J.Allen"),
    "DET": ("00-0032950", "J.Goff"),
    "SF": ("00-0036972", "B.Purdy"),
}


def _game(rng: np.random.Generator, season: int, week: int, gi: int, home: str, away: str) -> pd.DataFrame:
    n = 130
    qtr = np.repeat([1, 2, 3, 4], n // 4 + 1)[:n]
    qsr = np.concatenate([np.linspace(900, 0, (qtr == q).sum()) for q in (1, 2, 3, 4)])
    posteam = rng.choice([home, away], size=n)
    play_type = rng.choice(
        ["pass", "run", "punt", "field_goal", "kickoff", "no_play"],
        size=n,
        p=[0.5, 0.3, 0.07, 0.04, 0.06, 0.03],
    )
    is_pass = (play_type == "pass").astype(int)
    is_rush = (play_type == "run").astype(int)
    wp = np.clip(np.cumsum(rng.normal(0, 0.05, n)) + 0.5, 0.01, 0.99)
    wpa = np.diff(wp, prepend=wp[0])
    home_score = np.cumsum(rng.choice([0, 0, 0, 0, 3, 7], size=n))
    away_score = np.cumsum(rng.choice([0, 0, 0, 0, 3, 7], size=n))
    passer = np.where(is_pass == 1, [QBS[t][0] for t in posteam], None)
    passer_name = np.where(is_pass == 1, [QBS[t][1] for t in posteam], None)
    return pd.DataFrame(
        {
            "season": season,
            "season_type": "REG",
            "week": week,
            "game_id": f"{season}_{week:02d}_{away}_{home}",
            "game_date": pd.Timestamp(f"{season}-09-10") + pd.Timedelta(days=7 * (week - 1)),
            "play_id": np.arange(1, n + 1) * 10,
            "qtr": qtr,
            "quarter_seconds_remaining": qsr,
            "game_seconds_remaining": (4 - qtr) * 900 + qsr,
            "time": [f"{int(s // 60):02d}:{int(s % 60):02d}" for s in qsr],
            "down": rng.choice([1, 2, 3, 4], size=n, p=[0.45, 0.3, 0.17, 0.08]),
            "ydstogo": rng.integers(1, 11, size=n),
            "yardline_100": rng.integers(1, 100, size=n),
            "score_differential": home_score - away_score,
            "play_type": play_type,
            "pass": is_pass,
            "rush": is_rush,
            "wp": wp,
            "wpa": wpa,
            "vegas_wpa": wpa,
            "vegas_home_wp": wp,
            "home_wp": wp,
            "desc": "(shotgun) pass short right complete for 9 yards",
            "total_home_score": home_score,
            "total_away_score": away_score,
            "home_team": home,
            "away_team": away,
            "posteam": posteam,
            "passer_player_id": passer,
            "passer_player_name": passer_name,
            "passing_yards": np.where(is_pass == 1, rng.integers(-3, 40, size=n), np.nan),
            "touchback": np.where(play_type == "kickoff", rng.integers(0, 2, size=n), 0),
            "kickoff_fair_catch": 0,
            "kickoff_out_of_bounds": 0,
            "kickoff_downed": 0,
            "own_kickoff_recovery": 0,
        }
    )


@pytest.fixture(scope="session")
def nfl_dir(tmp_path_factory: pytest.TempPathFactory):
    d = tmp_path_factory.mktemp("nfl")
    rng = np.random.default_rng(7)
    frames, sched = [], []
    for season in (2023, 2024):
        for week in (1, 2):
            for gi, (home, away) in enumerate([("KC", "BUF"), ("DET", "SF")]):
                frames.append(_game(rng, season, week, gi, home, away))
                sched.append(
                    {
                        "season": season,
                        "game_type": "REG",
                        "week": week,
                        "game_id": f"{season}_{week:02d}_{away}_{home}",
                        "result": 3,
                    }
                )
    for season in (2023, 2024):
        pd.concat([f for f in frames if f["season"].iloc[0] == season]).to_parquet(
            d / f"pbp_{season}.parquet", index=False
        )
    pd.DataFrame(
        {
            "team_abbr": TEAMS,
            "team_name": ["Kansas City Chiefs", "Buffalo Bills", "Detroit Lions", "San Francisco 49ers"],
            "team_color": ["#E31837", "#00338D", "#0076B6", "#AA0000"],
            "team_color2": ["#FFB81C", "#C60C30", "#B0B7BC", "#B3995D"],
        }
    ).to_parquet(d / "teams.parquet", index=False)
    pd.DataFrame(sched).to_parquet(d / "schedules.parquet", index=False)
    return d


NBA_TEAMS = ["GSW", "LAL", "BOS", "SEA"]  # SEA exercises the old-tricode alias
NBA_PLAYERS = {
    201939: ("Curry", "GSW"),
    2544: ("James", "LAL"),
    951: ("Allen", "BOS"),
    1740: ("Lewis", "SEA"),
    999001: ("Nobody", "GSW"),
    999002: ("Someone", "LAL"),
}


def _shots(rng: np.random.Generator, season: int) -> pd.DataFrame:
    """Shots shaped like the nba_stats_shots feed: a season's worth of made/missed twos and threes."""
    n = 900
    pids = rng.choice(list(NBA_PLAYERS), size=n)
    three = rng.random(n) < (0.2 if season < 2010 else 0.4)
    dist = np.where(three, rng.integers(22, 30, size=n), rng.integers(0, 20, size=n))
    angle = rng.uniform(0, np.pi, size=n)
    x = np.round(dist * 10 * np.cos(angle)).astype(int)
    y = np.round(dist * 10 * np.sin(angle)).astype(int)
    made = rng.random(n) < np.where(three, 0.36, 0.5)
    return pd.DataFrame(
        {
            "game_id": [f"00{2}{season % 100:02d}00{i % 40:03d}" for i in range(n)],
            "season": season,
            "season_type_id": rng.choice(["2", "2", "2", "4"], size=n),
            "period": rng.integers(1, 5, size=n),
            "clock": "PT05M00.00S",
            "team_id": 1610612744,
            "team_tricode": [NBA_PLAYERS[p][1] for p in pids],
            "person_id": pids,
            "player_name": [NBA_PLAYERS[p][0] for p in pids],
            "action_type": np.where(made, "Made Shot", "Missed Shot"),
            "sub_type": "Jump Shot",
            "shot_result": np.where(made, "Made", "Missed"),
            "shot_value": np.where(three, 3, 2),
            "shot_distance": dist,
            "x_legacy": x,
            "y_legacy": y,
            "description": "Jump Shot",
            "score_home": "",
            "score_away": "",
        }
    )


@pytest.fixture(scope="session")
def nba_dir(tmp_path_factory: pytest.TempPathFactory):
    d = tmp_path_factory.mktemp("nba")
    rng = np.random.default_rng(11)
    for season in (1998, 1999, 2026, 2027):
        _shots(rng, season).to_parquet(d / f"shots_{season}.parquet", index=False)
    (d / "shots_stamp.txt").write_text("2027-01-15 08:51:21 EST\n", encoding="utf-8")
    (d / "teams.json").write_text(
        json.dumps(
            {
                "GSW": {"name": "Golden State Warriors", "color": "#fdb927", "color2": "#1d428a"},
                "LAL": {"name": "Los Angeles Lakers", "color": "#552583", "color2": "#fdb927"},
                "BOS": {"name": "Boston Celtics", "color": "#007a33", "color2": "#ba9653"},
                "OKC": {"name": "Oklahoma City Thunder", "color": "#007ac1", "color2": "#ef3b24"},
            }
        ),
        encoding="utf-8",
    )
    (d / "players.json").write_text(
        json.dumps({"201939": "Stephen Curry", "2544": "LeBron James"}), encoding="utf-8"
    )
    return d


@pytest.fixture
def make_ctx(nfl_dir, nba_dir):
    """Build a chart Context for a league over the synthetic feeds."""

    def _make(league: str) -> registry.Context:
        if league == "nfl":
            con = nfl.connect(
                pbp_glob=(nfl_dir / "pbp_*.parquet").as_posix(),
                teams_path=nfl_dir / "teams.parquet",
                schedules_path=nfl_dir / "schedules.parquet",
            )
            return registry.Context(league="nfl", con=con, current_season=2024)
        if league == "nba":
            con = nba.connect(shots_glob=(nba_dir / "shots_*.parquet").as_posix())
            extras = {
                "stamp_path": nba_dir / "shots_stamp.txt",
                "teams_path": nba_dir / "teams.json",
                "players_path": nba_dir / "players.json",
            }
            return registry.Context(league="nba", con=con, current_season=2027, extras=extras)
        raise ValueError(league)

    return _make


@pytest.fixture
def out_dirs(tmp_path, monkeypatch):
    charts_dir = tmp_path / "data" / "charts"
    monkeypatch.setattr(registry, "CHARTS_DIR", charts_dir)
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "data" / "registry.json")
    return tmp_path
