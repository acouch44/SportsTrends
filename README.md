# SportsTrends

Shareable sports data visualizations: multi-decade league trends (run vs pass, the 3-point
explosion, scoring eras) down to single-game play-by-play stories, for the NFL, NBA, NHL and MLB.

Every chart has its own link with a rich preview, downloadable PNGs sized for LinkedIn,
Instagram and Facebook, and (later) vertical video for TikTok / Reels / Shorts.

```
Python pipeline (src/sportstrends)                   Next.js static site (web/)
  st refresh  -> cache/raw/<league>/*.parquet
  st charts   -> data/charts/<league>/<slug>.json --> /<league>/<slug>  (share link + OG image)
  st captions -> social captions inside each bundle
  st render   -> og/<league>/<slug>.png (CI only)
```

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\st backfill --league nfl     # one-time: all seasons into cache/
.venv\Scripts\st charts  --league nfl      # write data/charts/nfl/*.json + data/registry.json
cd web; npm install; npm run dev           # http://localhost:3000
```

Data sources and their licenses are listed in [DATA_SOURCES.md](DATA_SOURCES.md).
