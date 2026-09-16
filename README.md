# Outer Sunset window sign census

A static dashboard for a block-by-block count of Prop G window signs in the
Outer Sunset — 45th Avenue west to the ocean, Lincoln Way south to Sloat.
Counted by hand on **9 September 2026**. The unit is the dwelling, not the
sign: a home showing three signs counts once, the same as a home showing one.

**Headline:** 224 homes showing a sign, across 145 blocks. No on G leads
185 to 39 — 4.7 to 1. Every block with homes on it was walked.

## Running it

No build step and no dependencies. Open `index.html` in a browser, or serve the
folder if you prefer:

```bash
python3 -m http.server 8777
```

Leaflet and the basemap tiles load over the network; everything else is local.

## The basemap

Tiles come from Esri's Light/Dark Gray Canvas at `server.arcgisonline.com`.
**No API key, no account, no token in the page** — the only requirement is the
attribution in the map's bottom-right corner, which is already there.

This was originally CARTO. CARTO now stamps "API KEY REQUIRED" diagonally
across tiles served to anonymous requests, while still returning `200 OK` —
so the failure is invisible to a status-code check and only shows up in the
pixels. If Esri ever does the same, the symptom will look identical, and the
fix is the `ESRI` constant near the top of `app.js`.

Esri's label layer doesn't name the cross streets at the zoom this map opens
at, so the page draws those labels itself from `data/blocks.geojson`.

If you ever want the map to be immune to a third party changing terms, the
repo already holds every street segment in the area in `data/_raw_streets.json`
— the street grid can be drawn directly from that with no tile server at all.

## Deploying

The whole folder is the site. Push it to GitHub Pages, drag it onto Netlify, or
point Cloudflare Pages at it — there is nothing to compile.

## Files

| Path | What it is |
| --- | --- |
| `index.html`, `style.css`, `app.js` | The page. Hand-edit freely. |
| `data/notes-raw.txt` | The field notes, verbatim, as recorded on 9 Sep 2026. |
| `data/counts.csv` | **The editable data.** One row per block. |
| `data/blocks.geojson` | Block geometry from SF's street centerline file. |
| `data/park.geojson` | The Great Highway roadway, drawn as Sunset Dunes. |
| `data/data.js` | Generated. Geometry + counts, joined, for the page to load. |
| `data/_raw_streets.json` | Cached DataSF response, so rebuilds work offline. |
| `assets/no-on-g.svg` | No on G campaign logo, shown in the headline bar. |
| `assets/yes-on-g.webp` | Yes on G campaign logo, shown in the headline bar. |
| `assets/favicon.svg` | Tab icon — a 🪧 emoji drawn as SVG text. |

## Changing a count

Edit `data/counts.csv`, then rebuild the bundle the page reads:

```bash
python3 scripts/bundle.py
```

Reload the page. That is the whole loop.

The `status` column controls how a block is treated:

- `counted` — included in the totals.
- `uncounted` — no count recorded; drawn as a dashed grey line.
- `not counted in notes` — same, but the notes explicitly marked it unusable.
- `no residences` — the block has no buildings, so it cannot hold a sign. This
  is complete information rather than a gap: it is drawn as a dotted line and
  kept out of every denominator on the page.
- `merged with previous block` — shares one observation with the block before
  it. Drawn in the same colour, tallied once, so totals don't double-count.

## Rebuilding from scratch

Only needed if the street geometry or the field notes change.

```bash
python3 scripts/build_blocks.py   # DataSF -> blocks.geojson + park.geojson
python3 scripts/parse_notes.py    # notes-raw.txt -> counts.csv  (OVERWRITES IT)
python3 scripts/bundle.py         # -> data.js
```

`parse_notes.py` regenerates `counts.csv` from the run-by-run mapping written
out at the top of that script, so it will discard hand edits to the CSV. If you
are correcting a single block, edit the CSV and run only `bundle.py`.

## Judgment calls in the parse

The notes are sequential walks, not keyed records, so a few blocks had to be
placed by inference. These are deliberately not shown on the page; they live
here, and each is commented where it is applied in `scripts/parse_notes.py`:

- Lower Great Highway was walked in two trips from opposite ends; the second is
  read south to north from Sloat. Santiago–Taraval there holds one building with
  no signs, so it closes that run at 0/0.
- The "S-t: 7/3" line sits under the "Great Highway" heading but does not belong
  to it. It records **48th Ave between Santiago and Taraval** — the block the
  48th Ave list stopped one short of — and is applied there.
- The "1/4" line in that same list belongs to **48th Ave between Taraval and
  Ulloa**. South of Santiago the frontage road and 48th Ave converge, and Lower
  Great Hwy has no buildings of its own along that stretch.
- On 47th Avenue, one observation spans Wawona to Vicente, which Cutler Avenue
  splits into two city blocks.

## Coverage

The census is complete: all 146 blocks with homes on them were walked.

Three blocks have no buildings at all, and are recorded as `no residences` rather
than as missing data — they are drawn as a dotted line and kept out of every
denominator on the page:

- Lower Great Hwy, Judah–Kirkham — those addresses face La Playa
- Lower Great Hwy, Taraval–Ulloa — the homes there front 48th Ave
- Lincoln Way, west of MLK Jr Drive — Beach Chalet frontage
