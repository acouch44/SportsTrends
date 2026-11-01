"""Draft the social copy for a chart with the Claude API.

The model never sees raw rows: it gets the chart's title, subtitle, hook, source line and the
compact ``summary`` block (first/last/min/max, biggest step, race leaders, key plays). Output is a
validated ``Social`` object written into the bundle with ``reviewed: false``. A bundle whose
captions were reviewed (``reviewed: true``) is never touched; an unreviewed one is redrafted only
when its ``data_through`` has moved on (or with ``--force``).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from .bundle import Social
from .charts.registry import load_bundle
from .config import SITE_URL

log = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"


class Captions(BaseModel):
    hook: str = Field(
        description="One line, at most 90 characters, that stops the scroll. A fact, not a tease."
    )
    alt_text: str = Field(
        description="Plain description of what the chart shows, for screen readers and link previews."
    )
    linkedin: str = Field(
        description="Two or three sentences. Analytical tone, one concrete number, no hashtags."
    )
    instagram: str = Field(description="One or two punchy lines, then a blank line, then 5-8 hashtags.")
    tiktok: str = Field(description="Under 150 characters, question-led or hot-take-led, 2-4 hashtags.")
    x: str = Field(description="At most 240 characters including one number and at most two hashtags.")
    hashtags: list[str] = Field(description="5-10 hashtags without the # sign, most specific first.")


SYSTEM = """You write social-media copy for SportsTrends, a site of data visualizations about the
NFL, NBA, NHL and MLB. Every post links to one chart. You are given the chart's title, subtitle, a
provisional hook, the data source and a compact summary of the numbers.

Rules:
- Only state numbers that appear in the summary. Round sensibly (54.3% -> 54%). Never invent context,
  causes, quotes or player/team details that are not in the input.
- Lead with the most surprising comparison (then vs now, before vs after a rule change, who leads).
- Plain, confident, specific. No emoji. No exclamation marks. No "Did you know".
- Percentages are shares of plays unless the summary says otherwise. Say "since 1999" or the actual
  span when the data starts after the sport did.
- Hashtags: the league, the sport, and the specific topic. No generic #data #viz tags.
"""


def _needs_draft(social: Social, data_through: str, force: bool) -> bool:
    if force:
        return True
    if social.reviewed:
        return False
    if not social.hook:
        return True
    return social.generated_for != data_through


def draft(bundle_json: dict) -> Captions | None:
    import anthropic

    client = anthropic.Anthropic()
    payload = {
        k: bundle_json.get(k)
        for k in ("league", "title", "subtitle", "hook", "kind", "data_through", "summary")
    }
    payload["source"] = bundle_json.get("source", {}).get("attribution")
    payload["url"] = f"{SITE_URL}/{bundle_json['league']}/{bundle_json['slug']}/"
    series_labels = {s["key"]: s["label"] for s in bundle_json.get("series", [])}
    if series_labels:
        payload["series_labels"] = series_labels

    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=2048,
        output_config={"effort": "medium"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        messages=[
            {"role": "user", "content": "Write the copy for this chart:\n\n" + json.dumps(payload, indent=1)}
        ],
        output_format=Captions,
    )
    if response.stop_reason == "refusal":
        log.warning(
            "%s: model declined (%s)", bundle_json.get("id"), getattr(response.stop_details, "category", None)
        )
        return None
    return response.parsed_output


def run(bundle_paths: list[Path], *, force: bool = False) -> int:
    n = 0
    for path in bundle_paths:
        b = load_bundle(path)
        if b is None or not _needs_draft(b.social, b.data_through, force):
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        caps = draft(raw)
        if caps is None:
            continue
        b.social = Social(**caps.model_dump(), reviewed=False, generated_for=b.data_through)
        path.write_text(b.model_dump_json(exclude_none=True) + "\n", encoding="utf-8", newline="\n")
        log.info("%s: captions drafted (hook: %s)", b.id, b.social.hook)
        n += 1
    return n
