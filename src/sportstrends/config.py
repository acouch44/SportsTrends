"""Paths, season logic and constants shared by every stage."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("ST_CACHE", ROOT / "cache"))
RAW = CACHE / "raw"
DATA = ROOT / "data"
CHARTS_DIR = DATA / "charts"
VENDOR_DIR = DATA / "vendor"
REGISTRY_PATH = DATA / "registry.json"
SCHEMA_DIR = ROOT / "schema"
WEB = ROOT / "web"

SITE_URL = os.environ.get("ST_SITE_URL", "https://sportstrends.vercel.app").rstrip("/")
UA = {"User-Agent": "sportstrends/0.1 (+https://github.com/acouch44/SportsTrends)"}

LEAGUES = ("nfl", "nba", "nhl", "mlb")


def current_season(league: str, today: date | None = None) -> int:
    """The season whose data file is still changing.

    NFL seasons are labelled by their starting year and begin in September. NBA and NHL files in
    the sportsdataverse mirror are labelled by the *ending* year and begin in October. MLB runs
    March-November under its calendar year. Out of season this returns the most recent completed
    season, so a refresh re-checks a file that no longer changes (cheap) instead of asking for one
    that does not exist yet.
    """
    today = today or date.today()
    y, m = today.year, today.month
    if league == "nfl":
        return y if m >= 9 else y - 1
    if league in ("nba", "nhl"):
        return y + 1 if m >= 10 else y
    if league == "mlb":
        return y if m >= 3 else y - 1
    raise ValueError(f"unknown league {league!r}")
