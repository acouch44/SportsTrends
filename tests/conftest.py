"""A tiny synthetic nflverse-shaped play-by-play so every chart can be computed offline in tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sportstrends.charts import registry
from sportstrends.sources import nfl

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
def fixture_dir(tmp_path_factory: pytest.TempPathFactory):
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


@pytest.fixture
def ctx(fixture_dir):
    con = nfl.connect(
        pbp_glob=(fixture_dir / "pbp_*.parquet").as_posix(),
        teams_path=fixture_dir / "teams.parquet",
        schedules_path=fixture_dir / "schedules.parquet",
    )
    return registry.Context(league="nfl", con=con, current_season=2024)


@pytest.fixture
def out_dirs(tmp_path, monkeypatch):
    charts_dir = tmp_path / "data" / "charts"
    monkeypatch.setattr(registry, "CHARTS_DIR", charts_dir)
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "data" / "registry.json")
    return tmp_path
