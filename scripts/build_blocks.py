#!/usr/bin/env python3
"""Build data/blocks.geojson: every countable block face in the census area.

Source: DataSF "Streets - Active and Retired" (resource 3psu-pn9h), one record
per block segment with from-street / to-street corner names.

Census area: 45th Ave west to the ocean, Lincoln Way south to Sloat Blvd.
Run once; the page reads only the generated GeoJSON.
"""
import json, os, re, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = "https://data.sf.gov/resource/3psu-pn9h.json"
BBOX = "within_box(line, 37.770, -122.520, 37.728, -122.498)"

# North-south streets walked, west to east. The frontage road is filed under
# streetname GREAT HWY but appears as LOWER GREAT HWY in corner names; the two
# long CNNs below are the actual highway -- that's Sunset Dunes, not a block.
PARK_CNNS = {"6436101", "6436201"}
NS_STREETS = ["GREAT HWY", "LA PLAYA", "48TH AVE", "47TH AVE", "46TH AVE", "45TH AVE"]

# A cross-street block counts only if both its corners are in this set.
CORNERS = {"45TH AVE", "46TH AVE", "47TH AVE", "48TH AVE", "LA PLAYA ST",
           "LOWER GREAT HWY", "MARTIN LUTHER KING JR DR", "CUTLER AVE"}

SUFFIX = re.compile(r"\s+(AVE|ST|BLVD|WAY|HWY|DR|TER|CT|RD)$")
# Short forms used in the join key -- stable, order-independent, never shown.
ALIAS = {"LOWER GREAT HWY": "LOWER GREAT", "LA PLAYA ST": "LA PLAYA",
         "MARTIN LUTHER KING JR DR": "MLK"}
# How those corners are written on the page.
DISPLAY = {"LOWER GREAT HWY": "Lower Great Hwy", "LA PLAYA ST": "La Playa",
           "MARTIN LUTHER KING JR DR": "MLK Jr Dr", "GREAT HWY": "Great Hwy"}


def norm(name):
    name = (name or "").strip().upper()
    return ALIAS.get(name) or SUFFIX.sub("", name)


def title(name):
    key = (name or "").strip().upper()
    if key in DISPLAY:
        return DISPLAY[key]
    out = " ".join(w.capitalize() for w in key.split())
    return re.sub(r"(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), out)


def display_street(streetname, cnn):
    if streetname == "GREAT HWY" and cnn not in PARK_CNNS:
        return "Lower Great Hwy"
    return title(streetname)


def fetch():
    raw = os.path.join(DATA, "_raw_streets.json")
    if os.path.exists(raw):
        return json.load(open(raw))
    q = urllib.parse.urlencode({"$limit": 6000, "$where": f"{BBOX} AND active=true"})
    with urllib.request.urlopen(f"{SRC}?{q}", timeout=90) as r:
        rows = json.load(r)
    json.dump(rows, open(raw, "w"))
    return rows


def span(coords, i):
    vals = [c[i] for c in coords]
    return min(vals), max(vals)


def drop_coarse(feats):
    """Lincoln Way and Sloat Blvd are divided roadways whose two sides are cut
    at different corners, so one record can span what another splits in two.
    Drop any segment that fully contains a different segment of the same street."""
    out = []
    for f in feats:
        lo, hi = span(f["coords"], 0)
        covered = any(
            g is not f and g["street"] == f["street"]
            and lo <= span(g["coords"], 0)[0] and span(g["coords"], 0)[1] <= hi
            and (hi - lo) > (span(g["coords"], 0)[1] - span(g["coords"], 0)[0]) + 1e-9
            for g in feats)
        if not covered:
            out.append(f)
    return out


def merge_midblock(feats):
    """DataSF splits Lower Great Hwy's Lawton-Moraga block at a MID BLOCK node.
    Residents count it as one block, so stitch the halves back together."""
    by, out = {}, []
    for f in feats:
        by.setdefault((f["street"], f["cnn"][:-3]), []).append(f)
    for (street, base), group in by.items():
        if len(group) == 2 and all("MID BLOCK" in (g["f_st"], g["t_st"]) for g in group):
            a, b = sorted(group, key=lambda g: g["cnn"])
            out.append({"cnn": base + "000", "street": street,
                        "f_st": a["f_st"] if a["f_st"] != "MID BLOCK" else b["f_st"],
                        "t_st": b["t_st"] if b["t_st"] != "MID BLOCK" else a["t_st"],
                        "coords": a["coords"] + b["coords"][1:]})
        else:
            out.extend(g for g in group if "MID BLOCK" not in (g["f_st"], g["t_st"]))
    return out


def dedupe_divided(feats):
    """Two one-way roadways per block on Lincoln Way. Keep the south side --
    the north side of Lincoln is Golden Gate Park, no houses."""
    by, out = {}, []
    for f in feats:
        by.setdefault((f["street"], *sorted([norm(f["f_st"]), norm(f["t_st"])])), []).append(f)
    for group in by.values():
        if len(group) > 1:
            group = [min(group, key=lambda g: sum(c[1] for c in g["coords"]) / len(g["coords"]))]
        out.extend(group)
    return out


def main():
    rows = [r for r in fetch() if r.get("line")]
    feats, park = [], []

    for r in rows:
        cnn, sname = r["cnn"], r.get("streetname", "")
        f_st, t_st = r.get("f_st", ""), r.get("t_st", "")
        if cnn in PARK_CNNS:
            park.append(r)
        elif sname in NS_STREETS or (f_st in CORNERS and t_st in CORNERS):
            feats.append({"cnn": cnn, "street": sname, "f_st": f_st, "t_st": t_st,
                          "coords": r["line"]["coordinates"]})

    feats = merge_midblock(feats)
    feats = drop_coarse(feats)
    feats = dedupe_divided(feats)

    out = []
    for f in feats:
        street = display_street(f["street"], f["cnn"])
        lo, hi = sorted([norm(f["f_st"]), norm(f["t_st"])])
        ns = f["street"] in NS_STREETS
        lats, lons = span(f["coords"], 1), span(f["coords"], 0)
        out.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": f["coords"]},
            "properties": {
                "cnn": f["cnn"], "street": street, "axis": "ns" if ns else "ew",
                "from": title(f["f_st"]), "to": title(f["t_st"]),
                "key": f"{norm(street.upper())}|{lo}|{hi}",
                "label": f"{street} between {title(f['f_st'])} and {title(f['t_st'])}",
                # Position along the street: avenues run north->south, cross
                # streets run west->east, matching the order of the field notes.
                "pos": -((lats[0] + lats[1]) / 2) if ns else (lons[0] + lons[1]) / 2,
            },
        })

    for f in out:
        f["properties"]["pos"] = round(f["properties"]["pos"], 6)
    out.sort(key=lambda f: (f["properties"]["axis"], f["properties"]["street"],
                            f["properties"]["pos"]))

    json.dump({"type": "FeatureCollection", "features": out},
              open(os.path.join(DATA, "blocks.geojson"), "w"), indent=1)
    json.dump({"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": p["line"]["coordinates"]},
         "properties": {"cnn": p["cnn"], "name": "Sunset Dunes"}} for p in park]},
        open(os.path.join(DATA, "park.geojson"), "w"), indent=1)

    from collections import Counter
    c = Counter((f["properties"]["axis"], f["properties"]["street"]) for f in out)
    print(f"{len(out)} blocks")
    for axis, lbl in (("ns", "AVENUES (north to south)"), ("ew", "CROSS STREETS (west to east)")):
        print(f"\n{lbl}")
        for (a, s), n in sorted(c.items()):
            if a == axis:
                print(f"  {s:<18} {n:>3}")


if __name__ == "__main__":
    main()
