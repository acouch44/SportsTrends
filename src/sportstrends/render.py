"""Screenshot the fixed-size render routes to PNG with Playwright.

The web app serves ``/render/<league>/<slug>/<format>/`` at an exact pixel size and sets
``data-render-ready="1"`` on the frame once the chart has drawn. Output lands at
``<out>/<format>/<league>/<slug>.png`` (so the ``og`` format becomes ``/og/nfl/<slug>.png`` on the
site). A sidecar ``.hash`` file lets unchanged bundles be skipped.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .charts.registry import load_bundle

log = logging.getLogger(__name__)

FORMATS: dict[str, tuple[int, int]] = {
    "og": (1200, 630),
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
}


def render_all(
    base: str, out: Path, formats: list[str], bundle_paths: list[Path], *, force: bool = False
) -> list[Path]:
    from playwright.sync_api import sync_playwright

    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        raise ValueError(f"unknown format(s) {unknown}; choose from {list(FORMATS)}")
    base = base.rstrip("/")
    written: list[Path] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for bp in bundle_paths:
                b = load_bundle(bp)
                if b is None:
                    continue
                for fmt in formats:
                    w, h = FORMATS[fmt]
                    dest = Path(out) / fmt / b.league / f"{b.slug}.png"
                    stamp = f"{b.code_version}:{b.data_through}:{fmt}:{w}x{h}"
                    hash_file = dest.with_suffix(".hash")
                    if not force and dest.exists() and hash_file.exists() and hash_file.read_text() == stamp:
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                    try:
                        page.goto(f"{base}/render/{b.league}/{b.slug}/{fmt}/", wait_until="networkidle")
                        page.wait_for_selector('[data-render-ready="1"]', timeout=30_000)
                        page.wait_for_timeout(250)  # fonts settle
                        page.screenshot(path=str(dest), full_page=False)
                    finally:
                        page.close()
                    hash_file.write_text(stamp)
                    written.append(dest)
                    log.info("%s %s -> %s (%.0f KB)", b.id, fmt, dest, dest.stat().st_size / 1024)
        finally:
            browser.close()
    return written
