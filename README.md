# SportsTrends

Shareable sports data visualizations: multi-decade league trends (run vs pass, the kickoff
return's comeback, the 4th-down revolution) down to the wildest game of the week, starting with
the NFL and built to take the NBA, NHL and MLB next.

Every chart has its own link with a preview image sized for LinkedIn, Facebook, X and Slack,
draft captions per platform, and a data-table twin.

```
Python pipeline (src/sportstrends)                      Next.js static site (web/)
  st refresh   -> cache/raw/<league>/*.parquet           (gitignored, nflverse mirror)
  st charts    -> data/charts/<league>/<slug>.json  -->  /<league>/<slug>/   share page + OG tags
               -> data/registry.json               -->  gallery, league pages, sitemap
  st captions  -> social captions inside each bundle -->  "Post it" panel
  st render    -> og/<league>/<slug>.png (CI only)  -->  link previews
```

## Charts

| Page | What it shows |
|---|---|
| `/nfl/pass-rate-era/` | Dropback rate since 1999: every play, game-in-doubt, early downs |
| `/nfl/kickoff-return-rate/` | Returned / touchback / fair-catch share of kickoffs, with every rule change |
| `/nfl/fourth-down-go-rate/` | 4th-and-short go-for-it rate by field zone |
| `/nfl/wp-rollercoaster/` | The highest-swing game of the last completed week (auto-updates) |
| `/nfl/passing-yards-race/` | Cumulative passing yards since 1999 as a bar-chart race |

## Run it locally

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python -m playwright install chromium

.venv\Scripts\st backfill --league nfl     # ~500 MB of play-by-play into cache/ (once)
.venv\Scripts\st charts  --league nfl      # data/charts/nfl/*.json + data/registry.json

cd web
npm install
npm run dev                                # http://localhost:3000
```

Social images, exactly as the nightly job makes them:

```powershell
cd web; npm run build; cd ..
.venv\Scripts\python -m http.server 3000 -d web/out      # in a second terminal
.venv\Scripts\st render --formats og,square,portrait,story
```

Captions need `ANTHROPIC_API_KEY` in the environment, then `st captions`. A bundle whose
`social.reviewed` is `true` is never rewritten; edit the JSON by hand and flip the flag.

## Deploying

The site is a static export deployed to Vercel **from GitHub Actions** (`.github/workflows/nightly.yml`),
so the rendered preview images ship with each deploy without being committed. One-time setup:

1. `npx vercel login`, then `cd web && npx vercel link` (creates `web/.vercel/project.json`).
2. Repository secrets: `VERCEL_TOKEN` (vercel.com/account/tokens), `VERCEL_ORG_ID` and
   `VERCEL_PROJECT_ID` (from `project.json`), and optionally `ANTHROPIC_API_KEY`.
3. Custom domain: set `NEXT_PUBLIC_SITE_URL` in the Vercel project's environment variables
   (the Actions build pulls it) so share links and preview-image URLs use it.
4. Actions tab, `nightly`, Run workflow. It refreshes the current season, rebuilds every chart,
   commits `data/`, builds, renders, deploys. It also runs every day at 10:30 UTC.

`backfill` is a manual workflow that warms the Actions cache with every season.

## Adding a chart

One Python module under `src/sportstrends/charts/<league>/`:

```python
@chart(ChartSpec(league="nfl", slug="my-chart", kind="line", title="...", source=nfl.SOURCE))
def compute(ctx: Context) -> dict:
    df = ctx.con.execute("SELECT season, ... FROM pbp WHERE ... GROUP BY season").df()
    return dict(encoding=..., series=[...], data=Table(columns=[...], rows=[...]),
                data_through=nfl.data_through(ctx.con))
```

`kind` picks the React component (`line`, `area`, `small_multiples`, `race`, `wp_story`,
`heatmap`); run `st charts --chart my-chart` and the page, gallery tile, render routes and
sitemap entry appear on the next build. `tests/test_charts.py` builds every registered chart
against a synthetic fixture.

Data sources and their licenses: [DATA_SOURCES.md](DATA_SOURCES.md).
