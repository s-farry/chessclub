"""Parse the 'League Tables' sheet of "Reconstructed historic league tables.xls"
into a long CSV (one row per player per table) for import_historical_tables.

Usage (needs xlrd, which reads legacy .xls):
    python historical/parse_historical_xls.py "Reconstructed historic league tables.xls" historical/historical_tables.csv

The sheet has one 8-column block per season (No, Name, Pld, W, D, L, Pts, spacer)
with divisions stacked down the rows. Commentary typed into the Name column is
kept as table notes, and "(taken from ...)" lines become the table's source.
"""
import sys, csv, xlrd
from collections import defaultdict
wb = xlrd.open_workbook(sys.argv[1]); sh = wb.sheet_by_index(0)
def cell(r,c):
    if c >= sh.ncols: return ""
    v = sh.cell_value(r,c); return v.strip() if isinstance(v,str) else v
def num(v):
    if v == "": return ""
    f = float(v); return int(f) if f.is_integer() else f

tables = []   # dicts: season, division, source, notes[], rows[]
for c0 in range(0, sh.ncols, 8):
    season = str(cell(4,c0))
    if not season: continue
    season_note = " ".join(str(x) for x in (cell(5,c0), cell(5,c0+3)) if x)
    cur = None; next_source = season_note; seen = defaultdict(int); note_open = False
    for r in range(6, sh.nrows):
        a, b = cell(r,c0), cell(r,c0+1)
        stats = [cell(r,c0+k) for k in range(2,7)]
        if isinstance(a,str) and a.isupper() and a != "NO" and b == "":
            seen[a] += 1
            div = a if seen[a] == 1 else f"{a} (alternative {seen[a]})"
            cur = dict(season=season, division=div, source=next_source, notes=[], rows=[])
            tables.append(cur); next_source = ""; note_open = False; continue
        if a == "No" or (a == "" and b == "" and all(s=="" for s in stats)):
            note_open = False; continue
        if isinstance(a,str) and a.startswith("("):     # source line for next table
            next_source = a; continue
        text = b if isinstance(b,str) else ""
        has_stats = a != "" or any(s != "" for s in stats)
        is_note = (not has_stats and text and
                   (note_open or text[0] in '("' or len(text.split()) > 3 or "'" in text and len(text.split())>2))
        if is_note:
            if cur["notes"] and note_open: cur["notes"][-1] += " " + text
            else: cur["notes"].append(text)
            note_open = not (text.endswith(")") or text.endswith('"')) ; continue
        note_open = False
        cur["rows"].append(dict(position=num(a), name=text, played=num(stats[0]), won=num(stats[1]),
                                drawn=num(stats[2]), lost=num(stats[3]), points=num(stats[4])))

with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["season","division","position","name","played","won","drawn","lost","points","source","table_notes"])
    for t in tables:
        for row in t["rows"]:
            w.writerow([t["season"], t["division"], *row.values(), t["source"], " | ".join(t["notes"])])

print(f"{len(tables)} tables, {sum(len(t['rows']) for t in tables)} player rows, "
      f"{len({r['name'] for t in tables for r in t['rows']})} distinct names\n")
for t in tables:
    flags = []
    unranked = sum(1 for r in t["rows"] if r["position"] == "")
    if unranked: flags.append(f"{unranked} unranked")
    for r in t["rows"]:
        p,wn,d,l = r["played"],r["won"],r["drawn"],r["lost"]
        if "" not in (p,wn,d,l) and p != wn+d+l: flags.append(f"{r['name']} P{p}!=W+D+L{wn+d+l}")
    print(f"{t['season']:32} {t['division']:28} {len(t['rows']):3} rows  {'; '.join(flags)}")
    for n in t["notes"]: print(f"{'':34}note: {n}")
