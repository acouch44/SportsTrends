"""``st``: the SportsTrends pipeline.

st backfill  --league nfl      all seasons into cache/ (one-time, or to rebuild the cache)
st refresh   --league nfl      the in-progress season only (nightly)
st charts    --league nfl      compute every registered chart -> data/charts + data/registry.json
st captions                    draft social copy for bundles that need it (Claude API)
st render    --base URL        screenshot the render routes to PNG (Playwright)
st all       --league nfl      refresh + charts + captions
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer

from . import config
from .charts import registry
from .sources import nba, nfl

app = typer.Typer(no_args_is_help=True, add_completion=False, help=__doc__)
log = logging.getLogger("st")

LEAGUE_MODULES = {"nfl": nfl, "nba": nba}

LeagueOpt = Annotated[str | None, typer.Option("--league", "-l", help="nfl | nba | nhl | mlb (default: all)")]
ChartOpt = Annotated[
    str | None, typer.Option("--chart", "-c", help="one chart id or slug, e.g. nfl/pass-rate-era")
]
ForceOpt = Annotated[bool, typer.Option("--force", help="ignore caches and hashes")]


def _setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _leagues(league: str | None) -> list[str]:
    if league is None:
        return list(LEAGUE_MODULES)
    if league not in LEAGUE_MODULES:
        raise typer.BadParameter(f"{league!r} is not wired up yet; choose from {', '.join(LEAGUE_MODULES)}")
    return [league]


def _fetch(league: str | None, *, current_only: bool, force: bool) -> None:
    for lg in _leagues(league):
        paths = LEAGUE_MODULES[lg].fetch(current_only=current_only, force=force)
        log.info("%s: %d files ready under %s", lg, len(paths), (config.RAW / lg).as_posix())


@app.command()
def backfill(league: LeagueOpt = None, force: ForceOpt = False) -> None:
    """Download every season (hundreds of MB) into cache/raw. Historical files are never re-fetched."""
    _setup_logging()
    _fetch(league, current_only=False, force=force)


@app.command()
def refresh(league: LeagueOpt = None, force: ForceOpt = False) -> None:
    """Re-check only the in-progress season (what the nightly job runs)."""
    _setup_logging()
    _fetch(league, current_only=True, force=force)


def _select(league: str | None, chart: str | None) -> list[registry.ChartDef]:
    defs = list(registry.load_all().values())
    if league:
        defs = [d for d in defs if d.spec.league == league]
    if chart:
        defs = [d for d in defs if d.spec.id == chart or d.spec.slug == chart]
        if not defs:
            raise typer.BadParameter(f"no chart matches {chart!r}")
    return defs


@app.command()
def charts(league: LeagueOpt = None, chart: ChartOpt = None) -> None:
    """Compute chart bundles from the cache and write data/charts, data/registry.json and the schema."""
    _setup_logging()
    defs = _select(league, chart)
    failures = 0
    for lg in sorted({d.spec.league for d in defs}):
        mod = LEAGUE_MODULES[lg]
        if not any((config.RAW / lg).glob("*.parquet")):
            log.error(
                "%s: nothing cached under %s. Run `st backfill --league %s` first.", lg, config.RAW / lg, lg
            )
            raise typer.Exit(2)
        ctx = registry.Context(league=lg, con=mod.connect(), current_season=config.current_season(lg))
        for d in [d for d in defs if d.spec.league == lg]:
            try:
                bundle = registry.build(d, ctx)
                path = registry.write_bundle(bundle)
                log.info(
                    "%s -> %s (%.0f KB, through %s)",
                    d.spec.id,
                    path.name,
                    path.stat().st_size / 1024,
                    bundle.data_through,
                )
            except Exception:  # keep going: one broken chart must not block the nightly refresh
                failures += 1
                log.exception("%s failed", d.spec.id)
    registry.write_registry()
    registry.write_schema(config.SCHEMA_DIR / "chart-bundle.schema.json")
    if failures:
        raise typer.Exit(1)


@app.command()
def captions(league: LeagueOpt = None, chart: ChartOpt = None, force: ForceOpt = False) -> None:
    """Draft hook + per-platform captions with the Claude API for bundles that lack reviewed ones."""
    _setup_logging()
    from . import captions as cap

    paths = [registry.bundle_path(d.spec.id) for d in _select(league, chart)]
    n = cap.run([p for p in paths if p.exists()], force=force)
    log.info("captions written for %d bundle(s)", n)
    registry.write_registry()


@app.command()
def render(
    base: Annotated[str, typer.Option(help="where the built site is being served")] = "http://localhost:3000",
    out: Annotated[
        Path, typer.Option(help="directory that receives <format>/<league>/<slug>.png")
    ] = config.WEB / "public",
    formats: Annotated[str, typer.Option(help="comma list of og,square,portrait,story")] = "og",
    league: LeagueOpt = None,
    chart: ChartOpt = None,
    force: ForceOpt = False,
) -> None:
    """Screenshot /render/<league>/<slug>/<format> for every bundle (skips unchanged ones)."""
    _setup_logging()
    from . import render as rnd

    paths = [registry.bundle_path(d.spec.id) for d in _select(league, chart)]
    written = rnd.render_all(
        base, out, [f.strip() for f in formats.split(",") if f.strip()], paths, force=force
    )
    log.info("%d image(s) written under %s", len(written), out)


@app.command()
def schema() -> None:
    """Write schema/chart-bundle.schema.json from the pydantic models."""
    p = registry.write_schema(config.SCHEMA_DIR / "chart-bundle.schema.json")
    typer.echo(str(p))


@app.command("all")
def all_(
    league: LeagueOpt = None,
    current_only: Annotated[bool, typer.Option(help="refresh (default) instead of backfill")] = True,
    with_captions: Annotated[bool, typer.Option(help="also run the caption step")] = True,
) -> None:
    """refresh (or backfill) -> charts -> captions."""
    _setup_logging()
    _fetch(league, current_only=current_only, force=False)
    charts(league=league, chart=None)
    if with_captions:
        captions(league=league, chart=None, force=False)


if __name__ == "__main__":
    app()
