"""Import reconstructed historical league tables (final standings only, no games).

    python manage.py import_historical_tables                 # dry run (default)
    python manage.py import_historical_tables --commit        # actually write

The whole import runs inside one transaction. Without --commit it is rolled back
at the end, so a dry run exercises exactly the same code path as a real import.

Each table becomes a League with historical=True, so standings are never
recalculated from (non-existent) games. Tables whose season already has a
regular (non-historical) league of the same division are skipped, as are tables
that have already been imported.

--fill-existing <slug> (repeatable) instead fills the standings of a league that is
already on the site but has no games (e.g. premiership-18-19, which only had
placeholder rows), and marks it historical so the numbers are not wiped again.
"""
import csv
import datetime
import difflib
import itertools
import re
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from league.models import League, Player, Season, Standings

HISTORICAL_DIR = Path(settings.BASE_DIR) / "historical"

# First season scored 3/1/0 (sheet note: "1st season with 3 for a win").
THREE_POINTS_FROM = 2001
# League.win_points etc. store choice codes from POINTS: 0->0, 1->0.5, 2->1, 3->2, 4->3
THREE_POINT_CODES = dict(win_points=4, draw_points=2, lost_points=0)
ONE_POINT_CODES = dict(win_points=2, draw_points=1, lost_points=0)

NICKNAMES = {
    "dave": "david", "ed": "edward", "eddie": "edward", "viv": "vivian",
    "jon": "jonathan", "mike": "michael", "phil": "philip", "tony": "anthony",
    "steve": "stephen", "bob": "robert", "stef": "stefan", "lenny": "leonard",
    "andy": "andrew", "jim": "james", "ken": "kenneth", "chris": "christopher",
    "greg": "gregory", "rick": "richard", "dan": "daniel", "danny": "daniel",
    "joe": "joseph", "tom": "thomas", "nick": "nicholas", "pete": "peter",
    "alex": "alexander", "sam": "samuel", "ron": "ronald", "fred": "frederick",
}


class DryRunRollback(Exception):
    pass


def norm(name):
    return re.sub(r"\s+", " ", name or "").strip().lower()


def loose_key(full_name):
    """(first name with nicknames expanded, surname), ignoring middle initials."""
    parts = norm(full_name).split()
    if len(parts) < 2:
        return None
    first = parts[0]
    if len(first) == 1:  # bare initial: too ambiguous to auto-match
        return None
    return NICKNAMES.get(first, first), parts[-1]


def season_years(label):
    """'2019-20 (aborted due to covid)' / '1999-2000' / '1996/97' -> (2019, 2020)."""
    y1 = int(re.match(r"\s*(\d{4})", label).group(1))
    return y1, y1 + 1


def division_title(division):
    m = re.match(r"(.*?) \(alternative \d+\)$", division)
    if m:
        return m.group(1).title() + " (alternative table)"
    return division.title()


def num(value, cast=float):
    value = (value or "").strip()
    if value == "":
        return None
    f = float(value)
    return int(f) if cast is int else f


class Command(BaseCommand):
    help = "Import historical final league tables (dry run unless --commit)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(HISTORICAL_DIR / "historical_tables.csv"))
        parser.add_argument("--aliases", default=str(HISTORICAL_DIR / "aliases.csv"))
        parser.add_argument("--commit", action="store_true",
                            help="Write to the database. Without this the import is rolled back.")
        parser.add_argument("--fill-existing", action="append", default=[], metavar="SLUG",
                            help="Fill the standings of this existing (game-less) league from the sheet "
                                 "and mark it historical. Can be given more than once.")
        parser.add_argument("--with-notes", action="store_true",
                            help="Also publish the spreadsheet's commentary notes in each league's description.")

    # ------------------------------------------------------------------ setup
    def load_aliases(self, path):
        aliases = {}
        with open(path, newline="") as f:
            lines = (line for line in f if not line.startswith("#"))
            for row in csv.DictReader(lines):
                target = (row.get("target") or "").strip()
                if target:
                    aliases[norm(row["spreadsheet_name"])] = target
        return aliases

    def handle(self, *args, **opts):
        csv_path, alias_path = Path(opts["csv"]), Path(opts["aliases"])
        for p in (csv_path, alias_path):
            if not p.exists():
                raise CommandError(f"{p} not found")
        self.aliases = self.load_aliases(alias_path)
        self.with_notes = opts["with_notes"]
        self.fill_slugs = set(opts["fill_existing"])

        with open(csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        tables = [
            (season, division, list(grp))
            for (season, division), grp in itertools.groupby(rows, key=lambda r: (r["season"], r["division"]))
        ]

        # existing players, indexed for matching
        self.players_by_id = {p.id: p for p in Player.objects.all()}
        self.exact = defaultdict(list)
        self.loose = defaultdict(list)
        for p in self.players_by_id.values():
            self.exact[norm(str(p))].append(p)
            k = loose_key(str(p))
            if k:
                self.loose[k].append(p)

        self.new_players = {}                 # canonical name -> Player
        self.new_player_tables = defaultdict(list)
        self.matches = defaultdict(set)       # how each spreadsheet name was resolved
        self.errors, self.warnings = [], []
        self.filled_slugs = set()
        report = dict(created=[], filled=[], skipped_existing=[], skipped_imported=[], skipped_empty=[], seasons_created=[])

        try:
            with transaction.atomic():
                for season_label, division, table_rows in tables:
                    self.import_table(season_label, division, table_rows, report)
                for slug in self.fill_slugs - self.filled_slugs:
                    self.errors.append(f"--fill-existing {slug}: no matching table in the spreadsheet")
                if self.errors:
                    raise DryRunRollback()
                if not opts["commit"]:
                    raise DryRunRollback()
        except DryRunRollback:
            committed = False
        else:
            committed = True

        self.print_report(report, committed, opts["commit"])

    # ----------------------------------------------------------- per table
    def get_season(self, label, report):
        y1, y2 = season_years(label)
        name = f"{y1}/{y2}"
        season = Season.objects.filter(name=name).first()
        if season is None:
            season = Season.objects.create(
                name=name,
                slug=f"{y1}-{y2}",
                start=datetime.date(y1, 9, 1),
                end=datetime.date(y2, 7, 31),
            )
            report["seasons_created"].append(name)
        return season

    def import_table(self, season_label, division, table_rows, report):
        tag = f"{season_label} {division}"
        players_rows = [r for r in table_rows if r["name"].strip()]
        if not players_rows:
            report["skipped_empty"].append(tag)
            return

        season = self.get_season(season_label, report)
        title = division_title(division)
        base = title.lower().replace(" (alternative table)", "")

        regular = [
            l for l in League.objects.filter(season=season, historical=False)
            if norm(l.name).replace("wallasey ", "") == base
        ]
        if regular and "(alternative" not in division and regular[0].slug in self.fill_slugs:
            self.fill_table(regular[0], tag, players_rows, report)
            return
        if regular and "(alternative" not in division:
            report["skipped_existing"].append(f"{tag}  (already on site as '{regular[0]}')")
            return

        slug = slugify(f"{title}-{season.slug}")
        existing = League.objects.filter(slug=slug).first()
        if existing is not None:
            if existing.historical:
                report["skipped_imported"].append(tag)
                return
            slug = slugify(f"{title}-{season.slug}-historical")

        y1, _ = season_years(season_label)
        points = THREE_POINT_CODES if y1 >= THREE_POINTS_FROM else ONE_POINT_CODES
        league = League.objects.create(
            name=title,
            season=season,
            slug=slug,
            historical=True,
            format=0,
            description=self.description(table_rows[0]),
            **points,
        )

        seen = {}
        for r in players_rows:
            player = self.resolve_player(r["name"].strip(), tag)
            if player.pk in seen:
                self.errors.append(
                    f"{tag}: '{r['name']}' and '{seen[player.pk]}' both resolve to {player} "
                    f"- an alias is probably wrong"
                )
                continue
            seen[player.pk] = r["name"]
            league.players.add(player)
            season.players.add(player)
            p, w, d, l = (num(r[k], int) for k in ("played", "won", "drawn", "lost"))
            if None not in (p, w, d, l) and p != w + d + l:
                self.warnings.append(f"{tag}: {r['name']} played {p} but W+D+L = {w + d + l}")
            Standings.objects.create(
                league=league,
                player=player,
                position=num(r["position"], int),
                matches=p, win=w, draws=d, lost=l,
                points=num(r["points"]),
            )
        report["created"].append(f"{tag:45} -> {league.name} {season.name} ({len(seen)} players)")

    def fill_table(self, league, tag, players_rows, report):
        """Fill an existing league's standings in place from the sheet."""
        self.filled_slugs.add(league.slug)
        if league.schedule_set.exists():
            self.errors.append(f"{tag}: {league.slug} has games; refusing to overwrite calculated standings")
            return
        existing = {st.player_id: st for st in Standings.objects.filter(league=league)}
        updated, added, seen = [], [], {}
        for r in players_rows:
            player = self.resolve_player(r["name"].strip(), tag)
            if player.pk in seen:
                self.errors.append(f"{tag}: '{r['name']}' and '{seen[player.pk]}' both resolve to {player}")
                continue
            seen[player.pk] = r["name"]
            p, w, d, l = (num(r[k], int) for k in ("played", "won", "drawn", "lost"))
            values = dict(position=num(r["position"], int), matches=p, win=w, draws=d, lost=l,
                          points=num(r["points"]))
            st = existing.get(player.pk)
            if st is None:
                st = Standings(league=league, player=player)
                added.append(str(player))
            else:
                updated.append(str(player))
            for k, v in values.items():
                setattr(st, k, v)
            st.save()
            league.players.add(player)
            league.season.players.add(player)
        untouched = [str(st.player) for pid, st in existing.items() if pid not in seen]
        if untouched:
            self.warnings.append(f"{tag}: in {league.slug} but not in the sheet (left as is): {', '.join(untouched)}")
        league.historical = True
        if not league.description:
            league.description = self.description(players_rows[0])
        league.save()
        report["filled"].append(
            f"{tag:45} -> filled existing {league.slug}: {len(updated)} rows updated, {len(added)} added, "
            f"{len(untouched)} not in sheet; marked historical"
        )

    def description(self, row):
        parts = []
        if row["source"]:
            source = row["source"].strip().strip("()")
            parts.append(f"<p><em>Reconstructed historical table, {source}.</em></p>")
        else:
            parts.append("<p><em>Reconstructed historical table.</em></p>")
        if self.with_notes and row["table_notes"]:
            items = "".join(f"<li>{n.strip()}</li>" for n in row["table_notes"].split(" | "))
            parts.append(f"<ul>{items}</ul>")
        return "\n".join(parts)

    # ----------------------------------------------------------- players
    def resolve_player(self, raw, tag):
        target = self.aliases.get(norm(raw))
        if target and target.startswith("#"):
            pid = int(target[1:])
            if pid not in self.players_by_id:
                raise CommandError(f"alias {raw!r} -> {target}: no such player id")
            player = self.players_by_id[pid]
            self.matches[raw].add(f"alias -> existing #{pid} {player}")
            return player
        name = target or raw
        how = f"alias -> '{name}', " if target else ""

        found = self.exact.get(norm(name), [])
        if len(found) == 1:
            if how or name != str(found[0]):
                self.matches[raw].add(f"{how}existing #{found[0].id} {found[0]}")
            else:
                self.matches[raw].add("exact")
            return found[0]
        if len(found) > 1:
            self.errors.append(f"{tag}: '{name}' matches several players {[p.id for p in found]}; add an alias")

        k = loose_key(name)
        found = self.loose.get(k, []) if k else []
        if len(found) == 1:
            self.matches[raw].add(f"{how}nickname/middle-initial -> existing #{found[0].id} {found[0]}")
            return found[0]
        if len(found) > 1:
            self.warnings.append(
                f"{tag}: '{name}' could be any of {[f'#{p.id} {p}' for p in found]}; created as new - add an alias"
            )

        player = self.new_players.get(norm(name))
        if player is None:
            first, _, last = name.partition(" ")
            player = Player.objects.create(name=first, surename=last or None)
            self.new_players[norm(name)] = player
        self.matches[raw].add(f"{how}NEW player")
        self.new_player_tables[name].append(tag)
        return player

    # ----------------------------------------------------------- report
    def print_report(self, report, committed, wanted_commit):
        out = self.stdout.write
        out("=" * 78)
        if committed:
            out(self.style.SUCCESS("COMMITTED: historical tables written to the database"))
        elif wanted_commit:
            out(self.style.ERROR("NOT COMMITTED: errors below must be fixed first (everything rolled back)"))
        else:
            out(self.style.WARNING("DRY RUN: nothing was written (rerun with --commit to import)"))
        out("=" * 78)

        out(f"\nSeasons to create ({len(report['seasons_created'])}): " + ", ".join(report["seasons_created"]))
        out(f"\nTables to import ({len(report['created'])}):")
        for t in report["created"]:
            out(f"  {t}")
        if report["filled"]:
            out(f"\nExisting leagues filled from the sheet ({len(report['filled'])}):")
            for t in report["filled"]:
                out(f"  {t}")
        out(f"\nSkipped, already on the site as a regular league ({len(report['skipped_existing'])}):")
        for t in report["skipped_existing"]:
            out(f"  {t}")
        if report["skipped_imported"]:
            out(f"\nSkipped, already imported ({len(report['skipped_imported'])}):")
            for t in report["skipped_imported"]:
                out(f"  {t}")
        out(f"\nSkipped, no players in table ({len(report['skipped_empty'])}): " + ", ".join(report["skipped_empty"]))

        matched = {n: h for n, h in self.matches.items() if h != {"exact"}}
        linked = sorted((n, h) for n, h in matched.items() if not any("NEW" in x for x in h))
        out(f"\nSpreadsheet names linked to existing players by alias/nickname ({len(linked)}):")
        for n, h in linked:
            out(f"  {n:24} {'; '.join(sorted(h))}")
        exact = sum(1 for h in self.matches.values() if h == {"exact"})
        out(f"\nSpreadsheet names matching an existing player exactly: {exact}")

        existing_names = [str(p) for p in self.players_by_id.values()]
        new_names = sorted(self.new_player_tables, key=lambda n: (n.split()[-1], n))
        out(f"\nNEW players to create ({len(new_names)}) - check for duplicates / people already on the site:")
        for n in new_names:
            seasons = sorted({t.split()[0] for t in self.new_player_tables[n]})
            span = seasons[0] if len(seasons) == 1 else f"{seasons[0]}..{seasons[-1]} ({len(seasons)} seasons)"
            similar = difflib.get_close_matches(n, existing_names + [x for x in new_names if x != n], n=3, cutoff=0.8)
            hint = f"   ~ similar: {', '.join(similar)}" if similar else ""
            out(f"  {n:26} {span}{hint}")

        if self.warnings:
            out(self.style.WARNING(f"\nWarnings ({len(self.warnings)}):"))
            for w in self.warnings:
                out(f"  {w}")
        if self.errors:
            out(self.style.ERROR(f"\nErrors ({len(self.errors)}):"))
            for e in self.errors:
                out(f"  {e}")
