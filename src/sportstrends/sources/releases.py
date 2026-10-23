"""GitHub-release data mirrors: nflverse-data and sportsdataverse-data.

Both publish one parquet per season as a release asset at a stable URL, regenerated nightly for
the season in progress and left alone afterwards. That makes the caching rule simple: historical
seasons are fetched once, the current season is re-checked every run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import RAW
from ..fetch import fetch_cached

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
SDV = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"

CURRENT_MAX_AGE_H = 6.0  # how often the in-progress season (or a season-less file) is re-checked


@dataclass(frozen=True)
class Asset:
    league: str
    name: str
    url: str  # may contain {season}
    first_season: int | None = None  # None for a single season-less file

    @property
    def seasonal(self) -> bool:
        return "{season}" in self.url

    def path(self, season: int | None = None) -> Path:
        ext = Path(self.url.split("?")[0]).suffix or ".parquet"
        stem = f"{self.name}_{season}" if self.seasonal else self.name
        return RAW / self.league / f"{stem}{ext}"

    def download(
        self, season: int | None = None, *, current_season: int | None = None, force: bool = False
    ) -> Path | None:
        url = self.url.format(season=season) if self.seasonal else self.url
        live = (not self.seasonal) or (
            current_season is not None and season is not None and season >= current_season
        )
        max_age = 0.0 if force else (CURRENT_MAX_AGE_H if live else None)
        return fetch_cached(url, self.path(season), max_age_h=max_age)
