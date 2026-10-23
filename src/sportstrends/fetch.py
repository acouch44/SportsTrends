"""Cached HTTP downloads (the pattern proven in the FantasyFootballInsights nflverse loader).

Rules: a file younger than ``max_age_h`` is never re-requested; an older one is re-requested with
``If-Modified-Since`` so an unchanged asset costs one 304; a failed request returns the stale copy
if there is one (stale beats nothing); bytes go to a ``.part`` file that is renamed into place, so
a killed run never leaves a truncated parquet behind.
"""

from __future__ import annotations

import logging
import os
import time
from email.utils import formatdate
from pathlib import Path

import requests

from .config import UA

log = logging.getLogger(__name__)


def fetch_cached(url: str, dest: Path, max_age_h: float | None = None, timeout: int = 300) -> Path | None:
    dest = Path(dest)
    headers = dict(UA)
    if dest.exists():
        age_h = (time.time() - dest.stat().st_mtime) / 3600
        if max_age_h is None or age_h < max_age_h:
            return dest
        headers["If-Modified-Since"] = formatdate(dest.stat().st_mtime, usegmt=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, headers=headers, timeout=timeout, stream=True) as r:
            if r.status_code == 304:
                os.utime(dest)  # unchanged upstream: restart the max-age clock
                return dest
            if r.status_code != 200:
                state = "stale copy kept" if dest.exists() else "no data"
                log.warning("GET %s -> %s (%s)", url, r.status_code, state)
                return dest if dest.exists() else None
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        tmp.replace(dest)
        log.info("fetched %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
        return dest
    except requests.RequestException as e:
        log.warning("GET %s failed: %s", url, e)
        tmp.unlink(missing_ok=True)
        return dest if dest.exists() else None
