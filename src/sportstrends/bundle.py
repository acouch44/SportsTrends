"""The chart bundle: the JSON contract between the Python pipeline and the web app.

One file per chart under ``data/charts/<league>/<slug>.json``. Pydantic owns the shape here;
``schema/chart-bundle.schema.json`` is emitted from these models and ``web/lib/bundle.ts`` mirrors
them in zod. Keep bundles small (< 300 KB): aggregates only, column-oriented rows.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Kind = Literal["line", "area", "heatmap", "race", "wp_story"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Axis(Strict):
    field: str
    type: Literal["quantitative", "temporal", "ordinal", "nominal"] = "quantitative"
    label: str = ""
    format: str | None = None  # d3-format / d3-time-format string


class Encoding(Strict):
    x: Axis
    y: Axis
    series: Axis | None = None


class Domain(Strict):
    x: list[float | str] | None = None
    y: list[float] | None = None


class Series(Strict):
    key: str
    label: str
    color: str | None = None  # hex, or a palette token like "accent"
    emphasis: bool = False


class Annotation(Strict):
    kind: Literal["vline", "hline", "point", "range", "text"]
    x: float | str | None = None
    y: float | None = None
    x2: float | str | None = None
    label: str = ""
    note: str | None = None


class Source(Strict):
    name: str
    url: str
    license: str = ""
    attribution: str = ""


class Social(Strict):
    hook: str = ""
    alt_text: str = ""
    linkedin: str = ""
    instagram: str = ""
    tiktok: str = ""
    x: str = ""
    hashtags: list[str] = Field(default_factory=list)
    reviewed: bool = False
    generated_for: str = ""  # data_through the captions were written against


class Table(Strict):
    columns: list[str]
    rows: list[list[Any]]


class Grid(Strict):
    shape: Literal["hex", "rect"] = "hex"
    bin_width: float
    x_range: list[float]
    y_range: list[float]
    court: str | None = None  # nba_halfcourt | nhl_rink | nfl_field
    value_label: str = ""
    cells: list[list[float]]  # [x, y, count, value]


class RankItem(Strict):
    key: str
    label: str
    value: float
    color: str | None = None
    group: str | None = None  # e.g. team abbreviation


class Frame(Strict):
    t: str
    ranks: list[RankItem]


class KeyPlay(Strict):
    elapsed: float  # seconds since kickoff
    qtr: int
    clock: str
    wp_before: float
    wp_after: float
    desc: str
    score: str  # "AWAY 17 - HOME 20" after the play


class Story(Strict):
    game_id: str
    season: int
    week: int
    date: str
    home: str
    away: str
    home_name: str = ""
    away_name: str = ""
    home_color: str = "#444444"
    away_color: str = "#999999"
    final: str = ""
    excitement: float = 0.0  # sum of |wpa| over the game
    key_plays: list[KeyPlay] = Field(default_factory=list)


class ChartBundle(Strict):
    schema_version: int = 1
    id: str
    league: str
    slug: str
    kind: Kind
    title: str
    subtitle: str = ""
    hook: str = ""
    tags: list[str] = Field(default_factory=list)
    source: Source
    generated_at: str
    data_through: str
    code_version: str = ""
    encoding: Encoding | None = None
    domain: Domain | None = None
    series: list[Series] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)
    data: Table | None = None
    grid: Grid | None = None
    frames: list[Frame] | None = None
    story: Story | None = None
    social: Social = Field(default_factory=Social)
    summary: dict[str, Any] = Field(default_factory=dict)  # compact facts for captions


class RegistryEntry(Strict):
    id: str
    league: str
    slug: str
    kind: Kind
    title: str
    subtitle: str = ""
    hook: str = ""
    tags: list[str] = Field(default_factory=list)
    data_through: str
    generated_at: str


class Registry(Strict):
    schema_version: int = 1
    generated_at: str
    charts: list[RegistryEntry]
