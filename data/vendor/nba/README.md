# Vendored NBA lookups

Small hand-maintained files that the shot feed does not carry.

- `teams.json`: tricode -> display name and two brand colours for the 30 current franchises, taken
  once from ESPN's public team listing (`site.api.espn.com/apis/site/v2/sports/basketball/nba/teams`)
  with ESPN abbreviations renamed to NBA tricodes (GSW, NOP, NYK, SAS, UTA, WAS). Old tricodes
  (SEA, NJN, NOH, NOK, VAN, CHH) are mapped to the current franchise in `sources/nba.py`.
- `players.json`: NBA `person_id` -> full name for every player who has ever ranked in the
  three-point race (the feed carries surnames only). Written by hand from the surname, teams and
  seasons in the data; a player missing from this file is shown by surname, so a new entrant never
  breaks the chart. Re-list candidates with the query in `charts/nba/three_pointers_race.py` and
  add any surname-only rows that appear.
