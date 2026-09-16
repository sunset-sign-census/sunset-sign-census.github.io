#!/usr/bin/env python3
"""Turn the field notes in data/notes-raw.txt into data/counts.csv, one row per block.

The notes are sequential walks, not keyed records, so this file states the
mapping explicitly: for each run, which street, which end it started from, and
the counts in order. Every assignment below is traceable to a line of the notes.

An entry is (yes, no) or (yes, no, span) where span>1 means the observation
covers that many city blocks and can't be split -- both blocks show the count,
but only the first is added to the totals. None means the block was walked past
without a usable count. NO_HOMES means the block has no residences at all, so
it can't hold a window sign -- that is complete information, not a data gap.
"""
import csv, json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

N2S, S2N, W2E = "n2s", "s2n", "w2e"
NO_HOMES = "no homes"

# (street, direction, entries, note)
RUNS = [
    # --- Lower Great Hwy, walked in two trips from opposite ends -------------
    # The "X/x" third entry is Judah-Kirkham, which has no buildings on it --
    # those addresses face La Playa instead.
    ("Lower Great Hwy", N2S, [
        (0, 0), (0, 1), NO_HOMES, (1, 3), (0, 3), (2, 0), (1, 1), (5, 3), (0, 2),
        (1, 0), (0, 0),
    ], "notes: 'Lgh' block, starting at Lincoln; Rivera-Santiago added later"),
    # The 'Great Highway' block is the same street walked back from Sloat. Its
    # last line, "S-t: 7/3", is NOT part of this run -- it records 48th Ave
    # between Santiago and Taraval, the block the 48th Ave list stopped short
    # of, and it is applied there instead. Santiago-Taraval on Lower Great Hwy
    # holds a single building with no signs, so it closes this run at 0/0.
    ("Lower Great Hwy", S2N, [
        (0, 1), (0, 1), (0, 2), (0, 9), NO_HOMES, (0, 0),
    ], "notes: 'Great Highway' block, starting at Sloat"),

    # --- Avenues ------------------------------------------------------------
    # '0/2 (up to v)' spans Wawona-Cutler and Cutler-Vicente; Cutler Ave splits
    # what the walker treated as one block. '(up to T)' is just a checkpoint.
    ("47th Ave", S2N, [
        (0, 0), (0, 2, 2), (0, 0), (0, 2), (0, 2), (0, 3), (0, 3), (0, 1),
        (0, 2), (0, 0), (0, 4), (1, 1), (1, 2), (0, 5), (0, 1), (0, 0),
    ], "notes: '47th', starting at Sloat"),
    # The eleven '48th' lines run Lincoln to Santiago. The twelfth block,
    # Santiago-Taraval, is the one recorded out of sequence as "S-t: 7/3".
    ("48th Ave", N2S, [
        (0, 5), (0, 1), (1, 5), (0, 2), (0, 2), (1, 5), (0, 1), (0, 2),
        (0, 4), (0, 2), (0, 1), (7, 3), (1, 4),
    ], "notes: '48th', starting at Lincoln; last two blocks recorded under the "
       "'S-t' line and the 'Great Highway' list"),
    ("46th Ave", S2N, [
        (0, 1), (0, 0), (0, 3), (0, 3), (0, 2), (0, 2), (0, 4), (0, 3),
        (0, 2), (0, 0), (0, 1), (0, 2), (0, 3), (0, 7), (1, 3), (0, 0),
    ], "notes: '46th', starting at Sloat"),
    ("45th Ave", N2S, [
        (1, 1), (1, 2), (0, 1), (0, 0), (0, 1), (1, 0), (0, 2), (0, 4),
        (0, 1), (0, 2), (0, 5), (0, 1), (1, 3), (0, 3), (2, 0), (0, 0),
    ], "notes: '45th', starting at Lincoln"),
    ("La Playa", N2S, [(6, 2), (0, 5), (0, 3)],
     "notes: 'Lp'; Judah-Kirkham added later, Irving-Judah revised to 5"),

    # --- Cross streets, each walked from the Great Highway eastward ---------
    ("Sloat Blvd",   W2E, [(0, 1), (0, 0), (0, 0)], "notes: 'Sloat'"),
    ("Wawona St",    W2E, [(0, 0), (0, 0), (0, 0)], "notes: 'W' (all nil)"),
    ("Vicente St",   W2E, [(0, 0), (0, 1), (0, 0)], "notes: 'V'"),
    ("Ulloa St",     W2E, [(0, 0), (0, 0), (1, 1)], "notes: 'U'"),
    ("Taraval St",   W2E, [(0, 0), (0, 0), (0, 0)], "notes: 'T' (nil)"),
    ("Santiago St",  W2E, [(0, 0), (0, 0), (0, 0), (0, 0)], "notes: 'S' (nil)"),
    ("Rivera St",    W2E, [(0, 0), (0, 0), (0, 0), (0, 1)], "notes: 'R'"),
    ("Quintara St",  W2E, [(0, 1), (0, 0), (0, 0), (0, 1)], "notes: 'Q'"),
    ("Pacheco St",   W2E, [(0, 0), (0, 0), (0, 0), (0, 0)], "notes: 'P' (nil)"),
    ("Ortega St",    W2E, [(0, 1), (0, 0), (0, 0), (0, 1)], "notes: 'O'"),
    ("Noriega St",   W2E, [(0, 2), (0, 1), (0, 0), (0, 0)], "notes: 'N'"),
    ("Moraga St",    W2E, [(0, 0), (0, 1), (2, 2), (0, 0)], "notes: 'M'"),
    ("Lawton St",    W2E, [(0, 0), (0, 0), (0, 0), (0, 1)], "notes: 'L' (first L)"),
    ("Kirkham St",   W2E, [(1, 0), (0, 3), (0, 1), (0, 0)], "notes: 'K'"),
    ("Judah St",     W2E, [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)], "notes: 'J' (nil)"),
    ("Irving St",    W2E, [(0, 0), (0, 1), (0, 1), (0, 0), (0, 0)], "notes: 'I'"),
    # Lincoln's westernmost block (Lower Great Hwy to MLK Jr Dr) is the Beach
    # Chalet frontage with no houses; the four counts start at MLK Jr Dr.
    ("Lincoln Way",  W2E, [NO_HOMES, (0, 0), (0, 0), (0, 1), (0, 0)],
     "notes: 'L' (second L); westernmost block is Beach Chalet frontage"),
    ("Cutler Ave",    W2E, [(0, 0)], "one-block stub off Lower Great Hwy"),
]

# Per-block annotations worth keeping. Only signs relevant to the measure are
# tallied; anything else recorded in the notes goes here, not into the counts.
BLOCK_NOTES = {
    "LOWER GREAT|JUDAH|KIRKHAM": "no buildings; these addresses face La Playa",
    "LOWER GREAT|SANTIAGO|TARAVAL": "one building, no signs",
    "LOWER GREAT|TARAVAL|ULLOA": "no buildings; the homes here front 48th Ave",
    "LINCOLN|LOWER GREAT|MLK": "no buildings; Beach Chalet frontage",
}


def main():
    blocks = json.load(open(os.path.join(DATA, "blocks.geojson")))["features"]
    by_street = defaultdict(list)
    for f in blocks:
        by_street[f["properties"]["street"]].append(f["properties"])
    for props in by_street.values():
        props.sort(key=lambda p: p["pos"])  # avenues N->S, cross streets W->E

    rows = {p["key"]: dict(p, yes="", no="", status="uncounted", note="", run="")
            for f in blocks for p in [f["properties"]]}
    problems = []

    for street, direction, entries, note in RUNS:
        seq = by_street.get(street)
        if not seq:
            problems.append(f"no geometry for street {street!r}")
            continue
        ordered = list(reversed(seq)) if direction == S2N else list(seq)
        span_total = sum(e[2] if isinstance(e, tuple) and len(e) > 2 else 1
                         for e in entries)
        if span_total > len(ordered):
            problems.append(f"{street} ({note}): {span_total} blocks of notes "
                            f"but only {len(ordered)} blocks exist")
            continue
        i = 0
        for entry in entries:
            span = entry[2] if isinstance(entry, tuple) and len(entry) > 2 else 1
            for j in range(span):
                # A run that already has data (the two Lower Great Hwy trips
                # meet in the middle) must not be overwritten.
                r = rows[ordered[i]["key"]]
                if r["status"] != "uncounted":
                    problems.append(f"overlap: {r['label']} assigned twice")
                if entry is NO_HOMES:
                    r["status"] = "no residences"
                elif entry is None:
                    r["status"] = "not counted in notes"
                else:
                    r.update(yes=entry[0], no=entry[1],
                             status="counted" if j == 0 else "merged with previous block")
                r["run"] = note
                i += 1

    for street, seq in by_street.items():
        missing = [p["label"] for p in seq if rows[p["key"]]["status"] == "uncounted"]
        if missing:
            problems.append(f"{street}: {len(missing)} block(s) with no count")
            problems.extend(f"    {m}" for m in missing)

    for key, txt in BLOCK_NOTES.items():
        if key in rows:
            rows[key]["note"] = txt
        else:
            problems.append(f"annotation for unknown block {key}")

    # Lower Great Hwy is walked from both ends; the two runs are laid down in
    # opposite directions, so the south-to-north trip must land on the blocks
    # the north-to-south trip didn't reach.
    out = sorted(rows.values(), key=lambda r: (r["axis"], r["street"], r["pos"]))
    with open(os.path.join(DATA, "counts.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, ["key", "cnn", "street", "from", "to", "label",
                                "axis", "yes", "no", "status", "note", "run"])
        w.writeheader()
        for r in out:
            w.writerow({k: r[k] for k in w.fieldnames})

    counted = [r for r in out if r["status"] == "counted"]
    y = sum(r["yes"] for r in counted)
    n = sum(r["no"] for r in counted)
    print(f"{len(out)} blocks total")
    print(f"  counted           {len(counted)}")
    print(f"  not counted       {sum(1 for r in out if r['status'] == 'uncounted')}")
    print(f"  no usable count   {sum(1 for r in out if r['status'] == 'not counted in notes')}")
    print(f"  no residences     {sum(1 for r in out if r['status'] == 'no residences')}")
    print(f"  merged w/ prev    {sum(1 for r in out if r['status'].startswith('merged'))}")
    print(f"\n  Yes on G: {y}   No on G: {n}   total {y + n}")
    print(f"  No on G share: {n / (y + n) * 100:.1f}%")
    if problems:
        print("\nNEEDS A LOOK:")
        for p in problems:
            print("  -", p)


if __name__ == "__main__":
    main()
