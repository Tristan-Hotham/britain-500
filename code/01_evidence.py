"""Step 1. Build the evidence catalogue for Britain and Ireland around AD 500.

Writes:
  data/evidence.csv        one row per mapped piece of evidence (all layers)
  data/hillforts_reused.csv Atlas of Hillforts records with dating evidence for AD 400 to 800
  data/hillforts_all_counts.csv  counts of all Atlas hillforts by nation and dating flag
  data/kingdoms.csv        approximate core areas of named kingdoms, with first written mentions
  data/civitates.csv       Roman-period peoples (civitates) placed at their Roman chief towns
  data/events.csv          dated events used on the timeline
  work/wd_items.json       Wikidata items in the frame (for the coverage figures)
Run: python3 code/01_evidence.py
"""
import collections, csv, gzip, json, os, re, sys
from common import *

ev = []          # evidence rows
def add(**k):
    k.setdefault("nation", nation_of(k["lat"], k["lon"]))
    ev.append(k)

# ------------------------------------------------------------------ Wikidata items (dedupe rows to items)
items = {}
for r in wd_rows("sites_by_class"):
    q = lit(r["s"])
    if not q.startswith("Q"):
        continue
    d = items.setdefault(q, {"q": q, "cls": set(), "inc": None, "per": set(), "pt": None})
    d["l"] = lit(r["sL"]); d["d"] = lit(r["desc"])
    d["pt"] = point(r["coord"]) or d["pt"]
    if r["clsL"]:
        d["cls"].add(lit(r["clsL"]))
    y = year(r["inc"])
    if y is not None:
        d["inc"] = y if d["inc"] is None else min(d["inc"], y)
    if r["periodL"]:
        d["per"].add(lit(r["periodL"]))
IT = [d for d in items.values() if d["pt"] and in_bbox(*d["pt"])]
print("Wikidata items in frame:", len(IT), "of", len(items))
WDU = lambda q: f"https://www.wikidata.org/wiki/{q}"
used = set()

def text(d):
    return (d.get("l") or "") + " | " + (d.get("d") or "")

def cent(t):
    """Date range from words like '6th century' or '7th-century' in a label or description."""
    m = re.findall(r"\b(5|6|7|fifth|sixth|seventh)(?:th)?[ -]centur", t, re.I)
    if not m:
        return None
    w = {"5": 5, "6": 6, "7": 7, "fifth": 5, "sixth": 6, "seventh": 7}
    cs = sorted(w[x.lower()] for x in m)
    return ((cs[0] - 1) * 100, cs[-1] * 100)

# ---------- 1. Anglo-Saxon (Germanic) cemeteries and settlements
GER = re.compile(r"anglo.?saxon|pagan saxon|saxon (?:cemetery|settlement|burial|inhumation|cremation|barrow)|anglian|grubenh|sunken.featured|early saxon", re.I)
GER_NOT = re.compile(r"middle saxon|late saxon|middle and late|late anglo|burh|church|cross|town|defence|boundary|palace|minster|chapel|charter|hunting lodge|fortified|dyke|offa|monastery|priory|abbey|sculpt|tower|wall\b|ditch", re.I)
for d in IT:
    t = text(d)
    if GER.search(t) and not GER_NOT.search(t) and not any(re.search("church|cross|chapel", c, re.I) for c in d["cls"]):
        nat = nation_of(*d["pt"])
        if nat not in ("England", "Scotland", "Wales"):
            continue
        c = cent(t)
        add(layer="germanic", culture="germanic", name=d["l"], lat=d["pt"][0], lon=d["pt"][1],
            d0=c[0] if c else 450, d1=c[1] if c else 650, dq="site" if c else "type",
            note=d["d"], src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])

# ---------- 2. ogham stones and sites (Wikidata, plus the Irish SMR), merged into find-spots
og = []
for d in IT:
    if any("gham" in c for c in d["cls"]) or re.search(r"\bogham\b", d["l"], re.I):
        if re.search(r"collection", " ".join(d["cls"]) + d["l"], re.I):
            continue
        og.append((d["pt"][0], d["pt"][1], d["l"], WDU(d["q"]), "Wikidata", d["q"]))
        used.add(d["q"])
smr = json.load(gzip.open(SMR))
SMR_COUNTS = collections.Counter(s["MONUMENT_CLASS"] for s in smr)
for s in smr:
    if s["MONUMENT_CLASS"] == "Ogham stone" and s["LATITUDE"] and in_bbox(float(s["LATITUDE"]), float(s["LONGITUDE"])):
        og.append((float(s["LATITUDE"]), float(s["LONGITUDE"]), f"Ogham stone, {s['TOWNLAND'].title()}, Co. {s['COUNTY'].title()}",
                   f"https://maps.archaeology.ie/HistoricEnvironment/?SMRID={s['ENTITY_ID']}", "Ireland SMR", s["ENTITY_ID"]))
print("ogham records before merging:", len(og))
# merge records within 300 m into one find-spot
og.sort(key=lambda r: (r[0], r[1]))
spots = []
for r in og:
    for s in spots:
        if abs(s["lat"] - r[0]) < 0.004 and km(s["lat"], s["lon"], r[0], r[1]) < 0.3:
            s["n"] += 1; s["srcs"].add(r[4]); s["names"].append(r[2]); break
    else:
        spots.append({"lat": r[0], "lon": r[1], "n": 1, "srcs": {r[4]}, "names": [r[2]], "url": r[3], "id": r[5]})
OGHAM_RECORDS = len(og)
for s in spots:
    nm = sorted(s["names"], key=lambda x: ("Site" not in x, len(x)))[0]
    add(layer="ogham", culture="irish", name=re.sub(r"\s*\(Ogham Site\)", "", nm), lat=s["lat"], lon=s["lon"], d0=400, d1=600, dq="type",
        note=f"{s['n']} record(s) at this find-spot", src=" and ".join(sorted(s["srcs"])), url=s["url"], id=s["id"], n=s["n"])

# ---------- 3. Latin and early Christian inscribed stones (Britain)
INS = re.compile(r"inscribed stone|inscribed stones|celtic inscribed", re.I)
for d in IT:
    if d["q"] in used:
        continue
    t = text(d)
    if (INS.search(t) or any("inscribed stone" in c.lower() for c in d["cls"])) and not re.search(r"cross.?inscribed|cross inscribed|incised|cross slab|cross-slab|pictish|symbol|runic|roman|ogham", t, re.I):
        nat = nation_of(*d["pt"])
        if nat in ("Republic of Ireland", "Northern Ireland", ""):
            continue
        if nat == "Scotland" and d["pt"][0] > 56.0:
            continue
        add(layer="latin", culture="brittonic", name=d["l"], lat=d["pt"][0], lon=d["pt"][1], d0=400, d1=700, dq="type",
            note=d["d"], src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])

# ---------- 4. Pictish stones
for d in IT:
    if d["q"] in used:
        continue
    t = text(d)
    if any(c == "Pictish stone" for c in d["cls"]) or re.search(r"pictish|symbol stone", t, re.I):
        if nation_of(*d["pt"]) != "Scotland" or re.search(r"broch|fort\b|church", t, re.I) and "Pictish stone" not in d["cls"]:
            continue
        add(layer="pictish", culture="pictish", name=d["l"], lat=d["pt"][0], lon=d["pt"][1], d0=500, d1=850, dq="type",
            note=d["d"], src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])

# ---------- 5. early churches and monasteries with a founding date AD 400 to 700 in Wikidata, and Irish early medieval ecclesiastical sites
for d in IT:
    if d["q"] in used:
        continue
    t = text(d); cls = " ".join(d["cls"]).lower()
    church = re.search(r"church|monast|chapel|abbey|priory|minster|ecclesiast|oratory|hermitage", cls + " " + t, re.I)
    if not church or re.search(r"temple|shrine|mithr|pictish|fort\b|hillfort", cls + " " + t, re.I):
        continue
    if d["inc"] is not None and 400 <= d["inc"] <= 700:
        y = d["inc"]
        d0, d1 = (y, y + 99) if y % 100 == 1 else (y, y)    # Wikidata stores "6th century" as 501
        add(layer="christian", culture="", name=d["l"], lat=d["pt"][0], lon=d["pt"][1], d0=d0, d1=max(d1, 700), dq="site",
            note=d["d"] + f" (Wikidata start date {y}{', read as a century' if y % 100 == 1 else ''})", src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])
    elif re.search(r"early medieval ecclesiastical site|early christian", t, re.I) and not re.search(r"cross|slab|memorial stone|inscribed", t, re.I):
        add(layer="christian", culture="", name=d["l"], lat=d["pt"][0], lon=d["pt"][1], d0=500, d1=1000, dq="type",
            note=d["d"] + " (no start date in Wikidata; early medieval)", src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])

# ---------- 6. other early medieval sites named as such (culture not assigned)
for d in IT:
    if d["q"] in used:
        continue
    t = text(d)
    if re.search(r"early medieval|early mediaeval|sub-roman|post-roman|dark age", d["l"], re.I) and not re.search(r"cross|sculpt|church|chapel|burh|urban|town|late anglo|roman frontier", t, re.I):
        c = cent(t)
        add(layer="other", culture="", name=d["l"], lat=d["pt"][0], lon=d["pt"][1], d0=c[0] if c else 400, d1=c[1] if c else 1000,
            dq="site" if c else "type", note=d["d"], src="Wikidata", url=WDU(d["q"]), id=d["q"])
        used.add(d["q"])

# ---------- 7. hillforts with dating evidence AD 400 to 800 (Atlas of Hillforts)
H = json.load(gzip.open(os.path.join(D15, "hillforts_atlas.json.gz")))
HF = [f["attributes"] for f in H["layers"]["Hillforts"]["features"]]
cnt = collections.Counter()
reused = []
for a in HF:
    em = a["Dating_Evidence__AD400___AD800"] == "Yes"
    cnt[(a["Country"], em)] += 1
    if em:
        reused.append(a)
        c = (a.get("Dating_Evidence__Comments") or "").strip()
        add(layer="hillfort", culture="", name=a["Name"], lat=a["Latitude"], lon=a["Longitude"], d0=400, d1=800, dq="site",
            note=(c[:420] + ("..." if len(c) > 420 else "")), src="Atlas of Hillforts", url=a.get("Atlas_URL") or "",
            id=f"atlas{a['Atlas_Number']}", nation=a["Country"])
rows = []
for a in reused:
    rows.append({"atlas_number": a["Atlas_Number"], "name": a["Name"], "country": a["Country"], "county": a.get("Historic_County") or a.get("Current_County_or_Unitary_Autho") or "",
                 "lat": round(a["Latitude"], 5), "lon": round(a["Longitude"], 5),
                 "dating_reliability": a["Dating_Evidence__Reliability"], "also_ad50_400": a["Dating_Evidence__AD50___AD400"], "also_400bc_ad50": a["Dating_Evidence__400BC___AD50"],
                 "also_post_ad800": a["Dating_Evidence__Post_AD800"], "enclosed_ha": a.get("Total_Enclosed_Area__ha_"), "promontory": a["Hillfort_Type__Promontory_Fort"],
                 "coastal": a["Topographic_Position__Coastal_P"], "altitude_m": a.get("Altitude__m_"),
                 "dating_comments": re.sub(r"\s+", " ", (a.get("Dating_Evidence__Comments") or "")).strip(), "atlas_url": a.get("Atlas_URL") or ""})
write_csv(os.path.join(DATA, "hillforts_reused.csv"), rows, list(rows[0].keys()))
hc = [{"country": c, "hillforts": cnt[(c, True)] + cnt[(c, False)], "dated_ad400_800": cnt[(c, True)]} for c in sorted({k[0] for k in cnt})]
write_csv(os.path.join(DATA, "hillforts_all_counts.csv"), hc, ["country", "hillforts", "dated_ad400_800"])
json.dump({"n": len(HF), "fields": [k for k in HF[0].keys()],
           "reliability": collections.Counter(a["Dating_Evidence__Reliability"] for a in reused),
           "also_ad50_400": sum(a["Dating_Evidence__AD50___AD400"] == "Yes" for a in reused),
           "also_post800": sum(a["Dating_Evidence__Post_AD800"] == "Yes" for a in reused),
           "also_iron_age": sum(a["Dating_Evidence__400BC___AD50"] == "Yes" or a["Dating_Evidence__800BC___400BC"] == "Yes" for a in reused),
           "promontory": sum(a["Hillfort_Type__Promontory_Fort"] == "Yes" for a in reused),
           "promontory_all": sum(a["Hillfort_Type__Promontory_Fort"] == "Yes" for a in HF),
           "coastal": sum(a["Topographic_Position__Coastal_P"] == "Yes" for a in reused),
           "coastal_all": sum(a["Topographic_Position__Coastal_P"] == "Yes" for a in HF),
           "area_med": float(np.nanmedian([a["Total_Enclosed_Area__ha_"] or np.nan for a in reused])),
           "area_med_all": float(np.nanmedian([a["Total_Enclosed_Area__ha_"] or np.nan for a in HF])),
           "radiocarbon_mentions": sum(bool(re.search(r"radiocarbon|C14|C-14|14C", a.get("Dating_Evidence__Comments") or "", re.I)) for a in reused)},
          open(os.path.join(WORK, "hillfort_stats.json"), "w"))

# ---------- 8. Roman towns and forts (Pleiades), context layer
pl_rows = []
for r in csv.DictReader(gzip.open(PLEIADES, "rt", encoding="utf-8")):
    try:
        la, lo = float(r["reprLat"]), float(r["reprLong"])
    except ValueError:
        continue
    if not in_bbox(la, lo):
        continue
    pl_rows.append(r)
    ft = {x.strip() for x in r["featureTypes"].split(",")}
    tp = {x.strip() for x in r["timePeriodsKeys"].split(",")}
    if not ("roman" in tp or "roman-britain" in tp):
        continue
    kind = "town" if ft & {"settlement", "fortified-settlement", "city-wall"} else "fort" if ft & {"fort", "fort-2"} else None
    if not kind or r["locationPrecision"] != "precise":
        continue
    late = "late-antique" in tp
    add(layer="roman", culture="", name=r["title"], lat=la, lon=lo, d0=43, d1=410, dq="context", kind=kind, late=int(late),
        note=f"Roman {kind}. Pleiades periods: {r['timePeriodsKeys'].replace(',', ', ')}." + (" Pleiades records it in the Late Antique period (AD 300 to 640)." if late else ""),
        src="Pleiades", url="https://pleiades.stoa.org" + r["path"], id="pl" + r["id"])

# ---------- 9. dykes (curated: early medieval or late Roman dates stated in the Wikipedia articles)
A = wiki_articles()
DYKES = [
    ("Wansdyke", "Wansdyke (earthwork)", "is a series of early medieval defensive linear earthworks", "Early medieval linear earthworks in Wiltshire and Somerset, the ditch facing north; one view cited in Wikipedia is that a sub-Roman authority built it. Its name (Woden's Dyke) occurs in 9th and 10th century charters. Point placed on Tan Hill, Wiltshire, which the article's photograph shows it crossing (OS Open Names).", 400, 700),
    ("Bokerley Dyke", "Bokerley Dyke", "In the 4th century it was remodelled and brought back into use", "Remodelled in the 4th century, perhaps in 367 to 368, and it may have stayed in use after Roman rule ended.", 360, 600),
    ("Devil's Dyke", "Devil's Dyke, Cambridgeshire", "thought to be of Anglo-Saxon origin", "Linear earthwork in Cambridgeshire, thought to be Anglo-Saxon; Roman finds under it point to a post-Roman date, and the similar Fleam Dyke has radiocarbon dates of AD 330 to 510 for its first phase.", 400, 700),
]
for nm, art, quote, note, d0, d1 in DYKES:
    check_quote(art, quote)
    c = A[art].get("coord")
    if c:
        la, lo = c[0]["lat"], c[0]["lon"]; srcp = "Wikipedia article coordinates"
    elif nm == "Wansdyke":   # no coordinates in the article or Wikidata download: Tan Hill, Wiltshire, from OS Open Names
        check_quote(art, "East Wansdyke is an impressive linear earthwork")
        la, lo = 51.38136, -1.8834; srcp = "OS Open Names, Tan Hill"
    else:   # look the name up in Wikidata
        cand = [d for d in IT if d["l"].lower() == nm.lower() or d["l"].lower().startswith(nm.lower() + " ")]
        assert cand, nm
        la, lo = cand[0]["pt"]; srcp = "Wikidata coordinates " + cand[0]["q"]
    add(layer="dyke", culture="", name=nm, lat=la, lon=lo, d0=d0, d1=d1, dq="site", note=note + f" ({srcp}.)", src="Wikipedia", url=wiki_url(art), id="dyke_" + nm)
# Fleam Dyke and Bran Ditch from Wikidata, if present
for nm in ("Fleam Dyke", "Bran Ditch", "Brent Ditch"):
    cand = [d for d in IT if d["l"].lower() == nm.lower()]
    if cand:
        add(layer="dyke", culture="", name=nm, lat=cand[0]["pt"][0], lon=cand[0]["pt"][1], d0=400, d1=700, dq="type",
            note="One of the Cambridgeshire dykes; Wikipedia's Devil's Dyke article gives a radiocarbon range of AD 330 to 510 for Fleam Dyke's first phase.",
            src="Wikidata", url=WDU(cand[0]["q"]), id=cand[0]["q"])

# ---------- 10. royal and high-status sites named in the stories (curated, each sentence checked against the article)
DUN = [d for d in IT if d["l"] == "Dunadd"]
ROYAL = [
    ("Tintagel", "Tintagel Castle", None, "uncovered the outlines of a palace from the 5th or early 6th century", "Clifftop site in Cornwall. Excavations in 2016 and 2017 uncovered the outlines of a palace of the 5th or early 6th century, with evidence of writing and goods from Spain and the eastern Mediterranean.", 450, 600, "brittonic"),
    ("Dinas Powys", "Dinas Powys hillfort", None, "re-inhabited by the time of Sub-Roman Britain in the 5th century", "Small hillfort near Cardiff, re-occupied by the 5th century; excavated by Leslie Alcock in 1954 to 1958.", 450, 700, "brittonic"),
    ("Cadbury Castle", "Cadbury Castle, Somerset", None, "including a \"Great Hall\"", "Iron Age hillfort in Somerset, refortified after Roman rule; Alcock's excavations of 1966 to 1970 found a great hall. Long linked with legends of Camelot.", 450, 600, "brittonic"),
    ("Dunadd", "Dunadd", DUN[0]["pt"] if DUN else None, "believed to be the capital of the ancient kingdom of Dál Riata", "Hillfort in Argyll believed to be the chief seat of Dál Riata, with a carved footprint and basin thought to be part of a king-making ritual.", 500, 800, "irish"),
    ("Dumbarton Rock (Alt Clut)", "Dumbarton Rock", None, "a letter that Saint Patrick wrote to King Ceretic of Alt Clut in the late 5th century", "The Rock of the Clyde, centre of the Brittonic kingdom later called Strathclyde. Saint Patrick wrote to its king, Ceretic, in the late 5th century.", 450, 870, "brittonic"),
    ("Bamburgh (Din Guaire)", "Bryneich", None, "Bamburgh is called Din Guaire in the Historia Brittonum", "Coastal rock in Northumberland, seat of the Bernician kings; the Historia Brittonum calls it Din Guaire. Ida is said to have taken the kingdom about 547.", 547, 800, "germanic"),
    ("Yeavering (Ad Gefrin)", "Yeavering", None, "in the year 627 Bishop Paulinus of York accompanied the Northumbrian king Edwin", "Royal estate of the Northumbrian kings with great timber halls; Bede says Paulinus preached and baptised here for 36 days in 627.", 550, 700, "germanic"),
    ("Sutton Hoo", "Sutton Hoo", None, "dating from the 6th to 7th centuries", "Two Anglo-Saxon cemeteries of the 6th to 7th centuries in Suffolk, with the great ship burial found in 1938.", 550, 650, "germanic"),
    ("Spong Hill", "Spong Hill", None, "largest known Early Anglo-Saxon cremation site", "The largest known early Anglo-Saxon cremation cemetery: 2,259 cremations and 57 inhumations, in use for about 150 years.", 420, 600, "germanic"),
    ("West Stow", "West Stow Anglo-Saxon village", None, "between the mid-5th century and the early 7th century", "Early Anglo-Saxon village in Suffolk, lived in from the mid 5th to the early 7th century: 69 sunken-featured buildings and 7 halls.", 450, 620, "germanic"),
]
check_quote("Bryneich", "about 547")
for nm, art, pt, quote, note, d0, d1, cul in ROYAL:
    check_quote(art, quote)
    if pt is None:
        c = A[art]["coord"] if art != "Bryneich" else A["Bamburgh Castle"]["coord"]
        pt = (c[0]["lat"], c[0]["lon"]); ps = "Wikipedia article coordinates"
    else:
        ps = "Wikidata coordinates"
    add(layer="royal", culture=cul, name=nm, lat=pt[0], lon=pt[1], d0=d0, d1=d1, dq="site", note=note + f" ({ps}.)",
        src="Wikipedia", url=wiki_url(art), id="royal_" + re.sub(r"\W+", "_", nm))

# ------------------------------------------------------------------ write evidence
# a Wikidata site that is also one of the hand-listed high-status sites is kept once, as the high-status site
roy = [r for r in ev if r["layer"] == "royal"]
ev = [r for r in ev if not (r["layer"] == "germanic" and any(km(r["lat"], r["lon"], q["lat"], q["lon"]) < 1.0 for q in roy))]
for i, r in enumerate(ev):
    r["lat"] = round(float(r["lat"]), 5); r["lon"] = round(float(r["lon"]), 5)
    r.setdefault("n", 1); r.setdefault("kind", ""); r.setdefault("late", "")
    r["name"] = re.sub(r"\s+", " ", r["name"]).strip()
    r["note"] = re.sub(r"\s+", " ", r.get("note") or "").strip()
    for k in ("name", "note"):
        r[k] = r[k].replace("\u2014", ", ").replace("\u2013", " to ").replace("--", ", ")
COLS = ["id", "layer", "culture", "name", "lat", "lon", "nation", "d0", "d1", "dq", "kind", "late", "n", "note", "src", "url"]
write_csv(os.path.join(DATA, "evidence.csv"), ev, COLS)
print(collections.Counter(r["layer"] for r in ev))
print(collections.Counter((r["layer"], r["nation"]) for r in ev))

# items in frame, for the coverage note
json.dump({"n_items_frame": len(IT), "n_items_all": len(items), "ogham_records": OGHAM_RECORDS, "ogham_spots": len(spots),
           "smr_ogham": SMR_COUNTS["Ogham stone"], "smr_ogham_present": SMR_COUNTS["Ogham stone (present location)"],
           "smr_ringfort": sum(v for k, v in SMR_COUNTS.items() if k.startswith("Ringfort")),
           "smr_ecclesiastical_enclosure": SMR_COUNTS.get("Ecclesiastical enclosure", 0),
           "pleiades_frame": len(pl_rows)}, open(os.path.join(WORK, "wd_items.json"), "w"))

# ------------------------------------------------------------------ kingdoms (approximate core areas)
# lat, lon: my own placement of a label at the place named in 'anchor' (approximate); r_km: size of the soft zone drawn.
# 'first' is the earliest written mention as the Wikipedia article states it; every quoted phrase is checked.
K = [
 # name, group, lat, lon, r_km, anchor, first written mention (my summary), article, phrase checked in the article
 ("Gododdin", "brittonic", 55.93, -2.85, 55, "between Din Eidyn (Edinburgh) and Traprain Law", "The name comes from the Votadini of Roman-period Greek texts; the kingdom is known from the poem Y Gododdin, set around 600 and surviving in a manuscript of the later 13th century.", "Gododdin", "Traprain Law and Din Eidyn"),
 ("Alt Clut (later Strathclyde)", "brittonic", 55.95, -4.56, 50, "Dumbarton Rock", "Saint Patrick's letter to Ceretic, king of Alt Clut, in the late 5th century.", "Kingdom of Strathclyde", "letter from Saint Patrick"),
 ("Rheged", "brittonic", 54.95, -3.3, 75, "the Solway, between Galloway and Carlisle (both proposed)", "Poems attributed to Taliesin call Urien \"Ruler of Rheged\" in the later 6th century; its borders are not described in any source.", "Rheged", "its borders are not described in any of them"),
 ("Elmet", "brittonic", 53.86, -1.15, 35, "Wikipedia article coordinates (Sherburn in Elmet area)", "Bede's silva Elmete and the Historia Brittonum, which says Edwin expelled its king Certic (early 7th century).", "Elmet", "occupied Elmet and expelled Certic"),
 ("Ebrauc", "brittonic", 53.96, -1.08, 30, "York (Eboracum)", "Doubtful as a kingdom: inferred from York's Roman name and later Welsh tradition.", "Ebrauc", "seat of a minor kingdom"),
 ("Gwynedd", "brittonic", 53.05, -4.05, 50, "Snowdonia and Anglesey", "The 5th-century Cantiorix inscription at Penmachno seems to be the earliest record of the name; Gildas attacks its king Maglocunus (Maelgwn).", "Kingdom of Gwynedd", "earliest record of the name"),
 ("Powys", "brittonic", 52.65, -3.25, 45, "the upper Severn (Welshpool)", "Its earliest rulers are known mainly from much later sources such as the Harleian genealogies.", "Kingdom of Powys", "known primarily from much later sources"),
 ("Pengwern", "brittonic", 52.71, -2.75, 22, "Shrewsbury", "Named in later Welsh poetry about Cynddylan (6th and 7th centuries); its exact location is unknown.", "Pengwern", "Its precise location is uncertain"),
 ("Dyfed", "brittonic", 51.9, -4.7, 40, "Wikipedia article coordinates", "Gildas attacks its king Vortipor; a stone at Castell Dwyran of about 550, in Latin and ogham, may name the same king. Its royal line was founded by Irish settlers.", "Kingdom of Dyfed", "founded by Irish settlers in the 5th century"),
 ("Brycheiniog", "brittonic", 51.95, -3.39, 25, "Brecon", "Founded in legend by Brychan in the mid 5th century; probably founded by Irish raiders in the late 5th century.", "Brycheiniog", "probably founded by Irish raiders"),
 ("Ergyng", "brittonic", 51.93, -2.75, 22, "Archenfield, near the Roman town of Ariconium", "Named after the Roman town of Ariconium; later called Archenfield by the English.", "Ergyng", "Archenfield"),
 ("Glywysing", "brittonic", 51.55, -3.45, 30, "Glamorgan", "Named in medieval Welsh tradition after an early king Glywys; descended from the Silures.", "Glywysing", "named after Glywys"),
 ("Gwent", "brittonic", 51.65, -2.85, 22, "Caerwent (Venta Silurum)", "The Silures article says their territory later developed into the 5th-century kingdoms of Gwent, Brycheiniog and Gwynllŵg.", "Silures", "5th-century Welsh kingdoms of Gwent"),
 ("Dumnonia", "brittonic", 50.6, -4.1, 85, "Devon and Cornwall", "Gildas (6th century) calls it Damnonia and attacks its ruler Constantine.", "Dumnonia", "used by Gildas in the 6th century"),
 ("Dál Riata", "irish", 56.08, -5.45, 55, "Dunadd", "Said to be founded by the legendary Fergus Mór in the 5th century; Dunadd is thought to be its capital.", "Dál Riata", "founded by the legendary king Fergus"),
 ("Picts (Fortriu)", "pictish", 57.5, -3.6, 90, "the Moray Firth", "The Verturiones were first documented by Ammianus Marcellinus in the late 4th century.", "Kingdom of Fortriu", "first documented in the late 4th century"),
 ("Bernicia", "germanic", 55.6, -1.72, 45, "Bamburgh", "The first Anglian king in the record is Ida, said to have taken the kingdom about 547.", "Bryneich", "about 547"),
 ("Deira", "germanic", 53.95, -0.6, 45, "the Yorkshire Wolds", "Bede wrote of Deira in his Ecclesiastical History, completed in 731.", "Deira", "Bede wrote of Deira"),
 ("Lindsey", "germanic", 53.25, -0.4, 35, "Lincoln (Lindum)", "Bede says Paulinus was received by the praefectus of Lindum in 625.", "Kingdom of Lindsey", "praefectus of Lindum"),
 ("East Angles", "germanic", 52.5, 1.0, 55, "Wikipedia article coordinates", "The first reference is in the Whitby Life of St Gregory, about 704 to 713.", "Kingdom of East Anglia", "Whitby Life of St Gregory"),
 ("Essex", "germanic", 51.75, 0.55, 40, "central Essex", "Bede notes Bishop Mellitus arriving in London in 604; a king list gives Æscwine from 527.", "Kingdom of Essex", "Mellitus in London in 604"),
 ("Kent", "germanic", 51.25, 1.0, 40, "Canterbury", "The earliest recorded king is Æthelberht, late 6th century; Augustine arrived in 597.", "Kingdom of Kent", "earliest recorded king of Kent was Æthelberht"),
 ("Sussex", "germanic", 50.9, -0.45, 40, "the Sussex coastal plain", "The foundation legend in the Anglo-Saxon Chronicle has Ælle landing in 477; historians are divided over whether he existed.", "Kingdom of Sussex", "Historians are divided over whether or not Ælle really existed"),
 ("Gewisse (later Wessex)", "germanic", 51.65, -1.17, 40, "Dorchester on Thames", "The name is first documented in the 8th century; their first location was the upper Thames around Dorchester.", "Gewisse", "first documented as Gewissorum in the eighth century"),
]
kr = []
for nm, g, la, lo, rk, anc, first, art, phrase in K:
    check_quote(art, phrase)
    kr.append({"name": nm, "group": g, "lat": la, "lon": lo, "r_km": rk, "anchor": anc, "first_written": first, "article": art, "url": wiki_url(art), "checked_phrase": phrase})
write_csv(os.path.join(DATA, "kingdoms.csv"), kr, list(kr[0].keys()))

# ------------------------------------------------------------------ civitates, placed at their Roman chief towns (Pleiades)
CIV = [("Dumnonii", "Isca Dumnoniorum", "79531"), ("Durotriges", "Durnovaria", "79431"), ("Belgae", "Venta Belgarum", "79734"), ("Atrebates", "Calleva Atrebatum", "79368"),
       ("Regni", "Noviomagus Reginorum", "79622"), ("Cantiaci", "Durovernum Cantiacorum", "79439"), ("Trinovantes", "Camulodunum", "79393"), ("Catuvellauni", "Verulamium", "79739"),
       ("Iceni", "Venta Icenorum", "79735"), ("Dobunni", "Corinium Dobunnorum", "79549"), ("Silures", "Venta Silurum", "79733"), ("Demetae", "Moridunum", "79602"),
       ("Cornovii", "Viroconium Cornoviorum", "79741"), ("Corieltauvi", "Ratae Corieltauvorum", "79651"), ("Parisi", "Petuaria", "79639"), ("Brigantes", "Isurium Brigantum", "89209")]
plid = {r["id"]: r for r in pl_rows}
cr = []
for tribe, town, pid in CIV:
    r = plid[pid]
    cr.append({"people": tribe, "town": town, "pleiades_title": r["title"], "lat": round(float(r["reprLat"]), 4), "lon": round(float(r["reprLong"]), 4),
               "url": "https://pleiades.stoa.org" + r["path"]})
write_csv(os.path.join(DATA, "civitates.csv"), cr, ["people", "town", "pleiades_title", "lat", "lon", "url"])
print("civitates placed:", len(cr), [c["pleiades_title"] for c in cr])

# ------------------------------------------------------------------ events (each phrase checked in the article)
EV = [
 (410, 410, "Roman rule ends", "The Romano-British depose Roman officials around 410; Honorius refuses Britain help.", "End of Roman rule in Britain", "deposed Roman officials around 410"),
 (429, 429, "Germanus visits", "Bishop Germanus of Auxerre visits Britain to combat Pelagianism.", "Germanus of Auxerre", "in or around 429"),
 (449, 449, "Hengist and Horsa (legend)", "The Anglo-Saxon Chronicle, compiled from the 9th century, dates their arrival to 449.", "Hengist and Horsa", "records that in the year 449"),
 (477, 477, "Ælle lands (legend)", "The Chronicle's foundation story of Sussex.", "Kingdom of Sussex", "in 477 Ælle and his three sons arrived"),
 (493, 516, "Badon", "A British victory; proposed dates include 493, 501 and 516.", "Battle of Badon", "Dates proposed by scholars for the battle include 493, 501 and 516"),
 (500, 545, "Gildas writes", "Usually dated to the 540s, now thought quite possibly earlier.", "De Excidio et Conquestu Britanniae", "some time in the 540s"),
 (536, 536, "The dust veil", "An eruption cools the northern hemisphere for several years.", "Volcanic winter of 536", "In early AD 536 (or possibly late 535)"),
 (541, 549, "Plague of Justinian", "Plague victims at Edix Hill near Cambridge show it reached Britain.", "Plague of Justinian", "show that it also reached Britain"),
 (547, 547, "Ida in Bernicia", "Said to have taken the kingdom about 547.", "Bryneich", "about 547"),
 (597, 597, "Augustine in Kent", "The Gregorian mission reaches Kent.", "Kingdom of Kent", "Gregorian mission in 597"),
 (600, 600, "Catraeth", "The Gododdin attack Catraeth, perhaps Catterick, around 600.", "Battle of Catraeth", "fought around AD 600"),
 (627, 627, "Paulinus at Yeavering", "Bede: 36 days of preaching and baptism at the royal vill.", "Yeavering", "in the year 627"),
]
er = []
for a0, a1, lab, note, art, phrase in EV:
    check_quote(art, phrase)
    er.append({"from": a0, "to": a1, "label": lab, "note": note, "article": art, "url": wiki_url(art)})
write_csv(os.path.join(DATA, "events.csv"), er, ["from", "to", "label", "note", "article", "url"])
for f in ("kingdoms.csv", "events.csv", "evidence.csv", "civitates.csv"):
    assert_clean(open(os.path.join(DATA, f), encoding="utf-8").read(), f)
print("done:", len(ev), "evidence rows")
