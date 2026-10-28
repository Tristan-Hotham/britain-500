"""Step 3. Statistics for the page, paper, blog and collage. Writes data/results.json (every number used anywhere),
data/kingdom_evidence.csv, data/longitude_profile.csv, data/timeline_counts.csv and work/site_data.json (the page's map data).
Run: python3 code/03_analyse.py
"""
import collections, json, math, os, random
import numpy as np
from common import *

ev = read_csv(os.path.join(DATA, "evidence.csv"))
for r in ev:
    r["lat"] = float(r["lat"]); r["lon"] = float(r["lon"]); r["d0"] = int(r["d0"]); r["d1"] = int(r["d1"])
K = read_csv(os.path.join(DATA, "kingdoms.csv"))
EVN = read_csv(os.path.join(DATA, "events.csv"))
CIV = read_csv(os.path.join(DATA, "civitates.csv"))
HS = json.load(open(os.path.join(WORK, "hillfort_stats.json")))
WI = json.load(open(os.path.join(WORK, "wd_items.json")))
LM = json.load(open(os.path.join(WORK, "layers_meta.json")))
HC = read_csv(os.path.join(DATA, "hillforts_all_counts.csv"))
R = {}
GB = ("England", "Wales", "Scotland")

# ---------------- counts
by = collections.Counter(r["layer"] for r in ev)
R["n_evidence"] = len(ev)
R["layers"] = dict(by)
R["n_mapped_not_roman"] = sum(v for k, v in by.items() if k != "roman")
R["layer_nation"] = {L: dict(collections.Counter(r["nation"] or "offshore" for r in ev if r["layer"] == L)) for L in by}
R["culture_points"] = dict(collections.Counter(r["culture"] for r in ev if r["culture"] and r["layer"] != "roman"))

# ---------------- hillforts
tot = sum(int(h["hillforts"]) for h in HC); dated = sum(int(h["dated_ad400_800"]) for h in HC)
R["hill"] = {"atlas_total": tot, "dated": dated, "share": dated / tot,
             "by_country": {h["country"]: {"n": int(h["hillforts"]), "dated": int(h["dated_ad400_800"]), "share": int(h["dated_ad400_800"]) / int(h["hillforts"])} for h in HC},
             "reliability": HS["reliability"], "reliable_ab": HS["reliability"].get("A - High", 0) + HS["reliability"].get("B - Medium", 0),
             "no_reliability": HS["reliability"].get("D - None", 0),
             "also_roman": HS["also_ad50_400"], "also_iron_age": HS["also_iron_age"], "also_post800": HS["also_post800"],
             "promontory": HS["promontory"], "promontory_share": HS["promontory"] / dated, "promontory_all_share": HS["promontory_all"] / tot,
             "coastal": HS["coastal"], "coastal_share": HS["coastal"] / dated, "coastal_all_share": HS["coastal_all"] / tot,
             "area_med": HS["area_med"], "area_med_all": HS["area_med_all"], "radiocarbon": HS["radiocarbon_mentions"]}
R["hill"]["coastal_ratio"] = R["hill"]["coastal_share"] / R["hill"]["coastal_all_share"]
R["hill"]["gb_dated"] = sum(R["hill"]["by_country"][c]["dated"] for c in GB)
R["hill"]["scotland_share_of_dated"] = R["hill"]["by_country"]["Scotland"]["dated"] / dated

# ---------------- east and west: Britain only (England, Wales and Scotland south of the Forth and Clyde)
def zone_pts(cul, south_only=True):
    return [r for r in ev if r["culture"] == cul and r["nation"] in GB and r["layer"] != "roman" and (not south_only or r["lat"] < 56.0)]
ger = zone_pts("germanic"); bri = zone_pts("brittonic")
R["eastwest"] = {"germanic_n": len(ger), "brittonic_n": len(bri),
                 "germanic_median_lon": float(np.median([r["lon"] for r in ger])), "brittonic_median_lon": float(np.median([r["lon"] for r in bri])),
                 "germanic_east_of_m2": sum(r["lon"] > -2 for r in ger) / len(ger), "brittonic_west_of_m3": sum(r["lon"] < -3 for r in bri) / len(bri)}
# share of Germanic among the culture-tagged evidence in Britain, by half-degree of longitude
prof = []
for x0 in np.arange(-6.0, 2.0, 0.5):
    g = sum(x0 <= r["lon"] < x0 + 0.5 for r in ger); b = sum(x0 <= r["lon"] < x0 + 0.5 for r in bri)
    prof.append({"lon_from": float(x0), "lon_to": float(x0 + 0.5), "germanic": g, "brittonic": b, "germanic_share": (g / (g + b)) if g + b else None})
write_csv(os.path.join(DATA, "longitude_profile.csv"), prof, ["lon_from", "lon_to", "germanic", "brittonic", "germanic_share"])
R["profile"] = prof
# the nearest Germanic site to each Latin stone and vice versa
def nearest(a, bs):
    return min(km(a["lat"], a["lon"], b["lat"], b["lon"]) for b in bs)
dg = [nearest(b, ger) for b in bri]; db = [nearest(g, bri) for g in ger]
R["eastwest"]["brit_to_ger_med_km"] = float(np.median(dg)); R["eastwest"]["ger_to_brit_med_km"] = float(np.median(db))
R["eastwest"]["brit_within_50km_of_ger"] = int(sum(d <= 50 for d in dg)); R["eastwest"]["ger_within_50km_of_brit"] = int(sum(d <= 50 for d in db))
# overlap of the two density surfaces (cells where both are above 10% of their own 99th percentile)
G = np.load(os.path.join(WORK, "grids.npz"))
gm = json.loads(str(G["meta"]))
def norm(a):
    ref = np.percentile(a[a > 0], 99); return np.clip(a / ref, 0, 1)
ng, nb, ni, npi = norm(G["germanic"]), norm(G["brittonic"]), norm(G["irish"]), norm(G["pictish"])
lm = G["lm"]
th = 0.1
lat_rows = inv_merc_y((1 - 2 * (gm["y0"] + np.arange(gm["h"]) + .5) / (256 * 2 ** gm["z"])) * math.pi)
cell_km2 = ((2 * math.pi * 6378.137 / (256 * 2 ** gm["z"])) * np.cos(np.radians(lat_rows))) ** 2
area = lambda m: float((m * cell_km2[:, None]).sum())
R["surfaces"] = {"sigma_km": gm["sigma_km"], "threshold": th,
                 "germanic_km2": area(lm & (ng > th)), "brittonic_km2": area(lm & (nb > th)), "irish_km2": area(lm & (ni > th)), "pictish_km2": area(lm & (npi > th)),
                 "ger_brit_overlap_km2": area(lm & (ng > th) & (nb > th)), "land_km2": area(lm)}

# ---------------- Ireland and the west: ogham and inscribed stones
og = [r for r in ev if r["layer"] == "ogham"]
R["ogham"] = {"records": WI["ogham_records"], "spots": len(og), "by_nation": dict(collections.Counter(r["nation"] or "offshore" for r in og)),
              "ireland_share": sum(r["nation"] in ("Republic of Ireland", "Northern Ireland") for r in og) / len(og),
              "smr_ogham": WI["smr_ogham"], "smr_ogham_moved": WI["smr_ogham_present"]}
lat = [r for r in ev if r["layer"] == "latin"]
# Latin stones in the south-west Welsh counties (old Dyfed and its neighbours) using the ONS county layer
from shapely.geometry import shape, Point
cty = json.load(open(COUNTIES))
cshape = [(f["properties"]["county"], shape(f["geometry"])) for f in cty["features"]]
def county(r):
    p = Point(r["lon"], r["lat"])
    for n, g in cshape:
        if g.contains(p): return n
    return ""
lc = collections.Counter(county(r) for r in lat)
R["latin"] = {"n": len(lat), "by_nation": dict(collections.Counter(r["nation"] for r in lat)), "by_county": dict(lc.most_common()),
              "wales_share": sum(r["nation"] == "Wales" for r in lat) / len(lat),
              "dyfed": lc.get("Dyfed", 0), "gwynedd": lc.get("Gwynedd", 0),
              "glamorgan": sum(lc.get(c, 0) for c in ("West Glamorgan", "South Glamorgan", "Mid Glamorgan")),
              "cornwall_devon": lc.get("Cornwall", 0) + lc.get("Devon", 0)}
R["latin"]["dyfed_share"] = R["latin"]["dyfed"] / len(lat)
R["latin"]["dyfed_wales_share"] = R["latin"]["dyfed"] / R["latin"]["by_nation"]["Wales"]
R["pictish"] = {"n": by["pictish"], "wikipedia_survive": 350}
check_quote("Pictish stone", "About 350 objects classified as Pictish stones have survived")
check_quote("Ogham", "The largest number outside Ireland are in Pembrokeshire, Wales")

# ---------------- Roman towns and forts
ro = [r for r in ev if r["layer"] == "roman"]
R["roman"] = {"n": len(ro), "towns": sum(r["kind"] == "town" for r in ro), "forts": sum(r["kind"] == "fort" for r in ro),
              "late": sum(r["late"] == "1" for r in ro), "late_towns": sum(r["late"] == "1" and r["kind"] == "town" for r in ro),
              "late_forts": sum(r["late"] == "1" and r["kind"] == "fort" for r in ro)}
R["roman"]["late_share"] = R["roman"]["late"] / R["roman"]["n"]
R["roman"]["late_town_share"] = R["roman"]["late_towns"] / R["roman"]["towns"]
R["roman"]["late_fort_share"] = R["roman"]["late_forts"] / R["roman"]["forts"]
towns = [r for r in ro if r["kind"] == "town" and r["nation"] == "England"]
# Germanic sites: distance to the nearest Roman town, against random points on land in the same part of England
gd = [nearest(g, towns) for g in ger if g["nation"] == "England"]
from shapely.ops import unary_union
eng = unary_union([g for n, g in cshape if any(f["properties"]["county"] == n and f["properties"]["nation"] == "England" for f in cty["features"])])
from shapely.prepared import prep
pe = prep(eng)
rng = random.Random(500)
lon_lo, lon_hi = min(g["lon"] for g in ger), max(g["lon"] for g in ger)
lat_lo, lat_hi = min(g["lat"] for g in ger), max(g["lat"] for g in ger)
rp = []
while len(rp) < 2000:
    x, y = rng.uniform(lon_lo, lon_hi), rng.uniform(lat_lo, lat_hi)
    if pe.contains(Point(x, y)): rp.append({"lat": y, "lon": x})
rd = [nearest(p, towns) for p in rp]
R["roman"]["ger_town_med_km"] = float(np.median(gd)); R["roman"]["random_town_med_km"] = float(np.median(rd))
R["roman"]["ger_within_10km_town"] = sum(d <= 10 for d in gd) / len(gd); R["roman"]["random_within_10km_town"] = sum(d <= 10 for d in rd) / len(rd)
R["roman"]["england_towns"] = len(towns)

# ---------------- Christian sites
ch = [r for r in ev if r["layer"] == "christian"]
R["christian"] = {"n": len(ch), "dated": sum(r["dq"] == "site" for r in ch), "undated_irish": sum(r["dq"] == "type" for r in ch),
                  "by_nation": dict(collections.Counter(r["nation"] or "offshore" for r in ch))}
R["germanic"] = {"n": by["germanic"], "site_dated": sum(r["dq"] == "site" for r in ev if r["layer"] == "germanic")}

# ---------------- timeline: evidence in play at each date
years = list(range(400, 701, 10))
tl = []
for y in years:
    row = {"year": y}
    for L in ("hillfort", "germanic", "latin", "ogham", "pictish", "christian", "royal", "dyke", "other"):
        row[L] = sum(r["d0"] <= y <= r["d1"] for r in ev if r["layer"] == L)
        row[L + "_site"] = sum(r["d0"] <= y <= r["d1"] and r["dq"] == "site" for r in ev if r["layer"] == L)
    tl.append(row)
write_csv(os.path.join(DATA, "timeline_counts.csv"), tl, list(tl[0].keys()))
R["timeline_ad500"] = tl[10]
R["site_dated_total"] = sum(r["dq"] == "site" for r in ev if r["layer"] != "roman")
R["type_dated_total"] = sum(r["dq"] == "type" for r in ev if r["layer"] != "roman")

# ---------------- kingdoms: what evidence lies in each rough zone
ke = []
for k in K:
    la, lo, rk = float(k["lat"]), float(k["lon"]), float(k["r_km"])
    near = [r for r in ev if r["layer"] != "roman" and km(la, lo, r["lat"], r["lon"]) <= rk]
    c = collections.Counter(r["culture"] or "untyped" for r in near)
    lay = collections.Counter(r["layer"] for r in near)
    cul = {x: c.get(x, 0) for x in ("germanic", "brittonic", "irish", "pictish")}
    typed = sum(cul.values())
    match = (cul.get(k["group"], 0) / typed) if typed else None
    ke.append({"name": k["name"], "group": k["group"], "r_km": int(rk), "n": len(near), **cul, "untyped": c.get("untyped", 0),
               "hillforts": lay.get("hillfort", 0), "christian": lay.get("christian", 0), "matching_share": match})
write_csv(os.path.join(DATA, "kingdom_evidence.csv"), ke, list(ke[0].keys()))
R["kingdoms"] = {"n": len(K), "groups": dict(collections.Counter(k["group"] for k in K)), "zones": ke,
                 "empty": [k["name"] for k in ke if k["n"] == 0],
                 "no_typed": [k["name"] for k in ke if (k["germanic"] + k["brittonic"] + k["irish"] + k["pictish"]) == 0]}
R["kingdoms"]["n_brittonic"] = R["kingdoms"]["groups"].get("brittonic", 0)
R["kingdoms"]["n_germanic"] = R["kingdoms"]["groups"].get("germanic", 0)

# ---------------- coverage and sources
R["coverage"] = {"wd_items_frame": WI["n_items_frame"], "pleiades_frame": WI["pleiades_frame"], "smr_ringforts": WI["smr_ringfort"],
                 "lowland_km2": LM["lowland_km2"], "places_gb": LM["places_gb"], "places_other": LM["places_other"]}
R["events"] = EVN
R["n_events"] = len(EVN)
R["n_civitates"] = len(CIV)
R["meta"] = {"title": "Britain in AD 500: what the ground tells us", "doi": DOI, "page": PAGE, "repo": REPO, "blog": BLOG}

# ---------------- page data
L = {"hillfort": 0, "germanic": 1, "latin": 2, "ogham": 3, "pictish": 4, "christian": 5, "royal": 6, "dyke": 7, "roman": 8, "other": 9}
pts = []
for r in ev:
    note = r["note"]
    if len(note) > 300: note = note[:297].rsplit(" ", 1)[0] + "..."
    extra = (1 if r["kind"] == "fort" else 0) * 2 + (1 if r["late"] == "1" else 0) if r["layer"] == "roman" else int(r["n"] or 1)
    pts.append([L[r["layer"]], r["name"], round(r["lat"], 4), round(r["lon"], 4), r["d0"], r["d1"], 1 if r["dq"] == "site" else 0, r["nation"], note, r["src"], r["url"], extra])
site = {"pts": pts, "kingdoms": [[k["name"], k["group"], float(k["lat"]), float(k["lon"]), int(k["r_km"]), k["anchor"], k["first_written"], k["url"]] for k in K],
        "civ": [[c["people"], c["town"], float(c["lat"]), float(c["lon"]), c["url"]] for c in CIV],
        "events": [[int(e["from"]), int(e["to"]), e["label"], e["note"], e["url"]] for e in EVN],
        "timeline": tl, "profile": prof, "dens": LM["dens"], "hills": LM["hills"], "colours": LM["colours"],
        "kz": {k["name"]: [k["n"], k["germanic"], k["brittonic"], k["irish"], k["pictish"], k["untyped"]] for k in ke}}
s = json.dumps(site, ensure_ascii=False, separators=(",", ":"), default=lambda o: o.item())
assert_clean(s, "site_data")
open(os.path.join(WORK, "site_data.json"), "w", encoding="utf-8").write(s)
json.dump(R, open(os.path.join(DATA, "results.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=lambda o: o.item())
assert_clean(open(os.path.join(DATA, "results.json"), encoding="utf-8").read(), "results")
print(json.dumps({k: R[k] for k in ("layers", "hill", "eastwest", "surfaces", "ogham", "latin", "roman", "christian")}, indent=1, default=float)[:6000])
for k in ke: print(k)
print("site data KB", len(s) // 1024)
