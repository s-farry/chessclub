# Historical league tables

Final standings for internal league seasons from 1996/97 onwards, reconstructed from
AGM minutes, newsletters, printed tables and ECF rated games. There are no individual
games, so each table is stored as a `League` with `historical=True`. Standings are never
recalculated for historical leagues: the "update standings" admin action and the other
recalculation code paths skip them.

## Files

| File | What it is |
| --- | --- |
| `historical_tables.csv` | One row per player per table, parsed from the spreadsheet |
| `aliases.csv` | Maps spreadsheet spellings to existing players (`#id`) or to one canonical spelling |
| `parse_historical_xls.py` | Regenerates the CSV from "Reconstructed historic league tables.xls" (needs `xlrd`) |

## Adding them to a database (e.g. the live site)

Back up the database first. Then:

```bash
python manage.py migrate league                      # adds League.historical (0065)

python manage.py import_historical_tables            # dry run: read the report
python manage.py import_historical_tables --commit   # import

# the 2018/19 Premiership was on the site with placeholder rows only (no games, 0 points)
python manage.py import_historical_tables --fill-existing premiership-18-19            # dry run
python manage.py import_historical_tables --fill-existing premiership-18-19 --commit

python manage.py update_seasons_page                 # dry run: shows the HTML it will remove and add
python manage.py update_seasons_page --commit        # add the links to the "Previous Seasons" page
```

Both commands are dry runs unless given `--commit`.

**Check the dry run before committing on the live site.** The `#id` targets in `aliases.csv` are
player ids from the local database. If the live database's ids differ, the dry run's "linked to
existing players" list will show the wrong people. Fix the ids in `aliases.csv` and run the dry run again.

### What the import does

- Creates any missing seasons (1 Sep to 31 Jul, so the current season is unaffected).
- Skips tables already on the site as normal leagues (2018-19 Championship/Premiership and 2021-22 onwards).
- Skips tables that have already been imported, so it is safe to re-run.
- Links names to existing players: aliases first, then exact name, then nickname/middle-initial
  (only if exactly one player matches). It creates new players for the rest.
- Sets the points system (3/1/0 from 2001-02, 1/½/0 before).
- Puts the source in each league's Details tab. Add `--with-notes` to also publish the spreadsheet's
  commentary, which is off by default because some of it is candid.

### What update_seasons_page does

Writes a section, between `<!-- historical-tables:start ... -->` and `<!-- historical-tables:end -->`,
listing every season with a historical league (newest first) and links to all of its leagues.
Re-running it only replaces that section. On the first run it also replaces the hand-written
2019/2020 and 2018/2019 sections, because those seasons are now part of the generated list.
Seasons above it (2020/2021 onwards) are still edited by hand in the admin as before.
