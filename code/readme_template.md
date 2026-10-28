# Britain in AD 500: what the ground tells us

An evidence-led map of Britain and Ireland around AD 500. Reused hillforts, Anglo-Saxon graves, Latin and ogham stones, Pictish stones and early churches on one interactive map, with the kingdoms named in later sources shown only as approximate, labelled zones.

**Interactive version:** https://tristan-hotham.github.io/britain-500/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23735820

A data study by Dr Tristan Hotham (Independent researcher). Related: [Within sight](https://tristan-hotham.github.io/within-sight/), on lines of sight between hillforts.

## Headline results

- The map places {{n_mapped_not_roman|int}} pieces of early medieval evidence, plus {{layers.roman|int}} Roman towns and forts as context: {{layers.ogham|int}} ogham find-spots, {{layers.latin|int}} Latin inscribed stones, {{layers.pictish|int}} Pictish stones, {{layers.hillfort|int}} hillforts, {{layers.christian|int}} early churches and monasteries, {{layers.germanic|int}} Anglo-Saxon cemeteries and settlements, {{layers.royal|int}} high-status sites, {{layers.dyke|int}} dykes and {{layers.other|int}} other sites.
- {{hill.dated|int}} of the {{hill.atlas_total|int}} hillforts in the Atlas of Hillforts ({{hill.share|pct1}}) have dating evidence for AD 400 to 800; {{hill.by_country.Scotland.dated|int}} are in Scotland, and on the Isle of Man the share is {{hill.by_country.Isle of Man.share|pct}}.
- Reused hillforts are more often coastal ({{hill.coastal_share|pct}} against {{hill.coastal_all_share|pct}} of all hillforts) and more often promontory forts ({{hill.promontory_share|pct}} against {{hill.promontory_all_share|pct}}).
- In Great Britain south of the Forth, Anglo-Saxon sites have a median longitude of {{eastwest.germanic_median_lon|w2}} degrees west and Latin stones with British high-status sites {{eastwest.brittonic_median_lon|w2}} degrees west; {{eastwest.brit_within_50km_of_ger|int}} of {{eastwest.brittonic_n|int}} western sites has an Anglo-Saxon site within 50 km, and the smoothed density surfaces do not overlap.
- {{ogham.ireland_share|pct}} of {{ogham.spots|int}} ogham find-spots are in Ireland; {{latin.wales_share|pct}} of {{latin.n|int}} inscribed stones are in Wales, {{latin.dyfed|int}} of them in the old county of Dyfed.
- Anglo-Saxon sites in England lie a median {{roman.ger_town_med_km|f1}} km from the nearest Roman town, against {{roman.random_town_med_km|f1}} km for random points.
- {{kingdoms.n|int}} kingdoms are shown as uncertain zones, each with its earliest written mention as Wikipedia describes it. Zones in the south, east and Wales match their evidence; in the north the evidence says little.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
| - | - |
| `index.html` | The interactive page: map with evidence layers, time slider, culture haze, kingdom zones, map layers panel and place search; charts and tables. |
| `header.png` | Social card (1200 by 630). |
| `data/evidence.csv` | One row per mapped piece of evidence: layer, culture, name, coordinates, nation, date range and whether it is site-dated or type-dated, note, source and URL. |
| `data/hillforts_reused.csv` | The Atlas hillforts with dating evidence for AD 400 to 800, with the Atlas's dating note and reliability. |
| `data/hillforts_all_counts.csv` | All Atlas hillforts and dated ones, by country. |
| `data/kingdoms.csv` | Kingdom label positions, zone radii, anchors, first written mentions and the phrase checked in each Wikipedia article. |
| `data/kingdom_evidence.csv` | Evidence within each kingdom zone by tradition. |
| `data/civitates.csv` | Roman-period peoples placed at their chief towns (Pleiades). |
| `data/events.csv` | Dated events used on the timeline, with their Wikipedia articles. |
| `data/longitude_profile.csv`, `data/timeline_counts.csv` | Chart data. |
| `data/results.json` | Every number used anywhere. |
| `data/*.png`, `data/*.json` | Map layers: hill shading, low-lying land, culture densities, land, borders, Roman roads, place list. |
| `code/` | The analysis (see below). |
| `reddit/` | Collage and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Hillforts:** Atlas records flagged with dating evidence for AD 400 to 800.
- **Wikidata:** {{coverage.wd_items_frame|int}} items in the frame, filtered by type and wording into Anglo-Saxon sites, Latin inscribed stones, Pictish stones, early churches (start date 400 to 700) and other early medieval sites. Ogham records from Wikidata and Ireland's Sites and Monuments Record merged into find-spots within 300 m.
- **High-status sites, dykes, kingdoms and events:** hand lists, each tied to a phrase that the code checks against the downloaded Wikipedia text.
- **Dates:** {{site_dated_total|int}} site-dated, {{type_dated_total|int}} type-dated with typical ranges.
- **Haze:** Gaussian kernel density, {{surfaces.sigma_km|int}} km, per tradition, scaled to its own 99th percentile, land only.
- **Kingdom zones:** my approximate placements; not borders.

## Known limits

Wikidata coverage differs by country and heritage agency (English Anglo-Saxon cemeteries poorly named, Welsh inscribed stones well named, Welsh ogham recorded as inscribed stones). Ireland's record covers the Republic only. Many stones have moved. Type-dated ranges are broad. The haze shows where evidence is dense in the data, not where people lived.

## How to rerun

Inputs are read in place; paths are at the top of `code/common.py` (override with environment variables). Python 3 with numpy, scipy, shapely, pillow and matplotlib; xelatex for the paper; Playwright only for testing.

```
python3 code/01_evidence.py
python3 code/02_layers.py
python3 code/03_analyse.py
python3 code/04_build_site.py
FONT_DIR=path/to/fonts python3 code/05_header.py
FONT_DIR=path/to/fonts python3 code/06_figures.py
python3 code/07_paper.py
python3 code/08_release.py
FONT_DIR=path/to/fonts python3 reddit/collage.py
```

## Sources and licences

- Hillforts: Lock, G. and Ralston, I. (2017) Atlas of Hillforts of Britain and Ireland, https://hillforts.arch.ox.ac.uk, CC BY-SA 4.0.
- Sites: Wikidata, CC0.
- Ogham stones, Republic of Ireland: National Monuments Service, Sites and Monuments Record, CC BY 4.0.
- Roman places: Pleiades, CC BY 3.0.
- Texts, coordinates of named sites, events: English Wikipedia, CC BY-SA 4.0 (retrieved 28 October 2026).
- Roman roads: Itiner-e (de Soto and others 2025), Zenodo 17122148, CC BY 4.0.
- Elevation: AWS Terrain Tiles (Mapzen/Tilezen), https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- Coast and Ireland borders: Natural Earth, public domain. Great Britain nations: Office for National Statistics, OGL v3.
- Place names: OS Open Names, contains OS data © Crown copyright and database right 2026, OGL v3; GeoNames, CC BY 4.0.

**Licence.** Derived data in `data/`, the page text, paper and figures: CC BY-SA 4.0 (they build on the Atlas of Hillforts and Wikipedia). Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) Britain in AD 500: what the ground tells us. Mapping early medieval evidence and uncertain kingdoms in Britain and Ireland from open data. Zenodo. https://doi.org/10.5281/zenodo.23735820

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
