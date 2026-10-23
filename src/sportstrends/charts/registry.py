"""Chart registry: a ChartSpec + a compute function per chart, bundles written to data/.

A chart module does::

    @chart(ChartSpec(league="nfl", slug="pass-rate-era", kind="line", title=..., source=nfl.SOURCE))
    def compute(ctx: Context) -> dict:
        ...
        return dict(encoding=..., series=..., data=Table(...), data_through=..., annotations=[...])

``build`` merges the returned fields with the spec, stamps generated_at / code_version, carries
captions over from the previous bundle on disk, fills ``summary`` and validates the whole thing.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from ..bundle import ChartBundle, Kind, Registry, RegistryEntry, Source
from ..config import CHARTS_DIR, REGISTRY_PATH, ROOT


@dataclass(frozen=True)
class ChartSpec:
    league: str
    slug: str
    kind: Kind
    title: str
    source: dict[str, str]
    subtitle: str = ""
    hook: str = ""
    tags: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        return f"{self.league}/{self.slug}"


@dataclass
class Context:
    league: str
    con: duckdb.DuckDBPyConnection
    current_season: int
    extras: dict[str, Any] = field(default_factory=dict)


ComputeFn = Callable[[Context], dict[str, Any]]


@dataclass(frozen=True)
class ChartDef:
    spec: ChartSpec
    compute: ComputeFn


REGISTRY: dict[str, ChartDef] = {}


def chart(spec: ChartSpec) -> Callable[[ComputeFn], ComputeFn]:
    def deco(fn: ComputeFn) -> ComputeFn:
        if spec.id in REGISTRY:
            raise ValueError(f"duplicate chart id {spec.id}")
        REGISTRY[spec.id] = ChartDef(spec, fn)
        return fn

    return deco


def load_all() -> dict[str, ChartDef]:
    """Import every module under sportstrends.charts.<league> so their decorators run."""
    import sportstrends.charts as pkg

    for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if m.name.endswith(".registry"):
            continue
        importlib.import_module(m.name)
    return REGISTRY


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def code_version() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or "dev"
    except (OSError, subprocess.SubprocessError):
        return "dev"


def bundle_path(chart_id: str) -> Path:
    league, slug = chart_id.split("/", 1)
    return CHARTS_DIR / league / f"{slug}.json"


def load_bundle(path: Path) -> ChartBundle | None:
    if not path.exists():
        return None
    return ChartBundle.model_validate_json(path.read_text(encoding="utf-8"))


def build(cdef: ChartDef, ctx: Context) -> ChartBundle:
    spec = cdef.spec
    fields = cdef.compute(ctx)
    previous = load_bundle(bundle_path(spec.id))
    kwargs: dict[str, Any] = dict(
        id=spec.id,
        league=spec.league,
        slug=spec.slug,
        kind=spec.kind,
        title=spec.title,
        subtitle=fields.pop("subtitle", spec.subtitle),
        hook=fields.pop("hook", spec.hook),
        tags=list(spec.tags),
        source=Source(**spec.source),
        generated_at=now_iso(),
        code_version=code_version(),
    )
    if previous is not None:
        kwargs["social"] = previous.social  # captions survive data refreshes
    bundle = ChartBundle(**kwargs, **fields)
    if not bundle.summary:
        bundle.summary = summarize(bundle)
    return bundle


def write_bundle(bundle: ChartBundle) -> Path:
    path = bundle_path(bundle.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bundle.model_dump_json(exclude_none=True) + "\n", encoding="utf-8")
    return path


def write_registry() -> Path:
    entries: list[RegistryEntry] = []
    for p in sorted(CHARTS_DIR.glob("*/*.json")):
        b = load_bundle(p)
        if b is None:
            continue
        entries.append(
            RegistryEntry(
                id=b.id,
                league=b.league,
                slug=b.slug,
                kind=b.kind,
                title=b.title,
                subtitle=b.subtitle,
                hook=b.hook,
                tags=b.tags,
                data_through=b.data_through,
                generated_at=b.generated_at,
            )
        )
    entries.sort(key=lambda e: (e.league, e.title))
    reg = Registry(generated_at=now_iso(), charts=entries)
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(reg.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return REGISTRY_PATH


def write_schema(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ChartBundle.model_json_schema(), indent=2) + "\n", encoding="utf-8")
    return path


# --- compact facts for the caption writer -------------------------------------------------------


def _r(v: Any) -> Any:
    return round(v, 4) if isinstance(v, float) else v


def summarize(b: ChartBundle) -> dict[str, Any]:
    s: dict[str, Any] = {"kind": b.kind, "data_through": b.data_through}
    if b.data and b.encoding:
        cols = b.data.columns
        xi, yi = cols.index(b.encoding.x.field), cols.index(b.encoding.y.field)
        si = (
            cols.index(b.encoding.series.field)
            if b.encoding.series and b.encoding.series.field in cols
            else None
        )
        fi = (
            cols.index(b.encoding.facet.field)
            if b.encoding.facet and b.encoding.facet.field in cols
            else None
        )
        groups: dict[str, list[tuple[Any, float]]] = {}
        for row in b.data.rows:
            if row[yi] is None:
                continue
            key = " / ".join(str(row[i]) for i in (fi, si) if i is not None) or "value"
            groups.setdefault(key, []).append((row[xi], float(row[yi])))
        out: dict[str, Any] = {}
        for key, pts in groups.items():
            pts.sort(key=lambda p: p[0])
            lo = min(pts, key=lambda p: p[1])
            hi = max(pts, key=lambda p: p[1])
            pairs = list(zip(pts, pts[1:], strict=False))
            step = max(pairs, key=lambda ab: abs(ab[1][1] - ab[0][1])) if pairs else None
            out[key] = {
                "first": [pts[0][0], _r(pts[0][1])],
                "last": [pts[-1][0], _r(pts[-1][1])],
                "min": [lo[0], _r(lo[1])],
                "max": [hi[0], _r(hi[1])],
                "biggest_step": [step[0][0], step[1][0], _r(step[1][1] - step[0][1])] if step else None,
            }
        s["series"] = out
    if b.frames:
        first, last = b.frames[0], b.frames[-1]
        s["race"] = {
            "first_frame": first.t,
            "first_leader": [first.ranks[0].label, _r(first.ranks[0].value)] if first.ranks else None,
            "last_frame": last.t,
            "final_top5": [[r.label, _r(r.value)] for r in last.ranks[:5]],
        }
    if b.grid:
        s["grid"] = {"cells": len(b.grid.cells), "densest": sorted(b.grid.cells, key=lambda c: -c[2])[:5]}
    if b.story:
        st = b.story
        s["story"] = {
            "matchup": f"{st.away} at {st.home}",
            "final": st.final,
            "date": st.date,
            "week": st.week,
            "excitement": _r(st.excitement),
            "key_plays": [
                [k.qtr, k.clock, _r(k.wp_before), _r(k.wp_after), k.desc[:140]] for k in st.key_plays
            ],
        }
    if b.annotations:
        s["annotations"] = [[a.kind, a.x, a.label] for a in b.annotations]
    return s
