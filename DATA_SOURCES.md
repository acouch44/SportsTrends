# Data sources

Every chart names its source in its bundle (`source` block) and on the page. All sources below are
free, need no API key, and are read as parquet/CSV straight from public mirrors. Nothing is scraped
from a league website in the nightly job.

| League | Data | Where it comes from | Seasons | License / terms |
|---|---|---|---|---|
| NFL | Play-by-play, schedules, team colours | [nflverse-data](https://github.com/nflverse/nflverse-data) GitHub releases (`pbp/play_by_play_{season}.parquet`, `schedules/games.parquet`, `teams/teams_colors_logos.parquet`) | 1999 to today | CC-BY-4.0. Attribution: "Data: nflverse". |
| NBA | Shot locations, play-by-play, schedules | [sportsdataverse-data](https://github.com/sportsdataverse/sportsdataverse-data) releases (`nba_stats_shots`, `espn_nba_pbp`, `espn_nba_schedules`) | 1997 to today (shots), 2002 to today (pbp) | MIT-licensed mirror of public league feeds; credit sportsdataverse. |
| NBA | Team colours and full player names | `data/vendor/nba/` (see its README): ESPN's public team listing, and a hand-kept name list for the shot feed's player IDs | current | Small lookups; the shot feed carries surnames only. |
| NHL | Play-by-play with shot coordinates and expected goals, shootouts, schedules | sportsdataverse-data releases (`nhl_pbp_full`, `nhl_shootout`, `nhl_schedules`) | 2010-11 to today | As above. |
| NHL | Shot-level expected goals (optional overlay) | [MoneyPuck](https://moneypuck.com/data.htm) season zips, fetched by hand during a backfill only | 2007-08 to today | Non-commercial; credit MoneyPuck; no automated scraping. |
| MLB | Statcast pitch-level data | sportsdataverse-data releases (`mlb_statcast`) | 2015 to today | Mirror of Baseball Savant exports; credit MLB Advanced Media / Baseball Savant. |
| MLB | Season team totals back to 1871 | Lahman Baseball Database `Teams.csv`, vendored under `data/vendor/lahman/` | 1871 to last season | CC BY-SA 3.0 (Sean Lahman). |
| MLB | Game logs, time of game, play-by-play | [Retrosheet](https://www.retrosheet.org/downloads/) CSV downloads | 1897 to last season | Free, with this notice: "The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org." |

Raw downloads live under `cache/` and are never committed. Only the small aggregated bundles under
`data/charts/` and the registry are in git.
