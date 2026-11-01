from __future__ import annotations

import json

import pytest

from sportstrends.bundle import ChartBundle, Registry, Social
from sportstrends.charts import registry

MAX_BUNDLE_BYTES = 300 * 1024


def _defs():
    return list(registry.load_all().values())


@pytest.mark.parametrize("cdef", _defs(), ids=lambda d: d.spec.id)
def test_chart_builds_valid_bundle(cdef, make_ctx, out_dirs):
    ctx = make_ctx(cdef.spec.league)
    bundle = registry.build(cdef, ctx)
    assert bundle.id == cdef.spec.id
    assert bundle.data_through
    assert bundle.summary
    path = registry.write_bundle(bundle)
    assert path.stat().st_size < MAX_BUNDLE_BYTES
    reloaded = ChartBundle.model_validate_json(path.read_text(encoding="utf-8"))
    assert reloaded.kind == bundle.kind
    if bundle.kind in ("line", "area", "wp_story"):
        assert bundle.data and bundle.encoding
        assert bundle.encoding.x.field in bundle.data.columns
        assert bundle.encoding.y.field in bundle.data.columns
    if bundle.kind == "race":
        assert bundle.frames and all(f.ranks for f in bundle.frames)
    if bundle.kind == "heatmap":
        assert bundle.grid and bundle.grid.cells and all(len(c) == 4 for c in bundle.grid.cells)
    if bundle.kind == "wp_story":
        assert bundle.story and bundle.story.key_plays


def test_captions_survive_refresh(make_ctx, out_dirs):
    ctx = make_ctx("nfl")
    cdef = next(d for d in _defs() if d.spec.slug == "kickoff-return-rate")
    first = registry.build(cdef, ctx)
    first.social = Social(hook="hand-written", reviewed=True)
    registry.write_bundle(first)
    second = registry.build(cdef, ctx)
    assert second.social.hook == "hand-written" and second.social.reviewed


def test_registry_lists_every_bundle(make_ctx, out_dirs):
    for cdef in _defs():
        registry.write_bundle(registry.build(cdef, make_ctx(cdef.spec.league)))
    path = registry.write_registry()
    reg = Registry.model_validate_json(path.read_text(encoding="utf-8"))
    assert {e.id for e in reg.charts} == {d.spec.id for d in _defs()}


def test_schema_emits(tmp_path):
    p = registry.write_schema(tmp_path / "s.json")
    schema = json.loads(p.read_text())
    assert schema["title"] == "ChartBundle"
    assert "kind" in schema["properties"]
