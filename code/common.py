"""Shared paths and helpers for Britain in AD 500.

Inputs are read in place (override any path with an environment variable of the same name):
  D15      folder with hillforts_atlas.json.gz and ad500_bundle.json.gz
  SMR      Republic of Ireland Sites and Monuments Record (JSON, CC BY 4.0)
  PLEIADES pleiades-places-latest.csv.gz (CC BY 3.0)
  NE       Natural Earth geojson folder
  COUNTIES GB counties with nation (ONS, OGL v3)
  OSNAMES  OS Open Names GB (OGL v3), tab separated
  CITIES   GeoNames cities1000.zip (CC BY 4.0), for places in Ireland and the Isle of Man
  DEM_BIN, DEM_IDX  AWS Terrain Tiles at zoom 10 (see dem.py)
  ITINERE  Itiner-e Roman roads, Britain subset (CC BY 4.0)
"""
import csv, gzip, io, json, math, os, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(ROOT, "work")
os.makedirs(WORK, exist_ok=True)

E = os.environ.get
D15 = E("D15", "/home/claude/hist/_data15")
SMR = E("SMR", "/home/claude/hist/_data10/ireland_smr_all.json.gz")
PLEIADES = E("PLEIADES", "/mnt/user-data/uploads/Downloads/pleiades-places-latest.csv.gz")
NE = E("NE", "/home/claude/hist/_data3/ne/geojson")
COUNTIES = E("COUNTIES", "/home/claude/hist/how-roman-is-your-road/data/counties.geojson")
OSNAMES = E("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
CITIES = E("CITIES", "/mnt/user-data/uploads/Downloads/cities1000.zip")
ITINERE = E("ITINERE", "/home/claude/hist/how-roman-is-your-road/data/itinere_gb.geojson")

SLUG = "britain-500"
DOI = "10.5281/zenodo.23735820"
PAGE = f"https://tristan-hotham.github.io/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
BLOG = f"https://blog.tristanhotham.com/2026/10/28/{SLUG}/"

# map frame: Britain, Ireland and the Isle of Man
BBOX = (-11.0, 49.8, 2.1, 61.0)   # lon0, lat0, lon1, lat1


def wd_rows(name):
    b = bundle()
    t = b["queries"][name]["tsv"].split("\n")
    h = [x.lstrip("?") for x in t[0].split("\t")]
    return [dict(zip(h, l.split("\t"))) for l in t[1:] if l]


_B = None
def bundle():
    global _B
    if _B is None:
        _B = json.load(gzip.open(os.path.join(D15, "ad500_bundle.json.gz")))
    return _B


def lit(v):
    """Strip RDF literal syntax: '"x"@en' -> x, '<http://.../Q1>' -> Q1."""
    v = (v or "").strip()
    if v.startswith("<http://www.wikidata.org/entity/"):
        return v.rsplit("/", 1)[1].rstrip(">")
    m = re.match(r'^"(.*)"(?:@\w+|\^\^.*)?$', v, re.S)
    return m.group(1) if m else v


def point(v):
    m = re.search(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", v or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


def year(v):
    m = re.search(r'"?(-?\d{3,4})-\d\d-\d\d', v or "")
    return int(m.group(1)) if m else None


def in_bbox(lat, lon):
    return BBOX[1] <= lat <= BBOX[3] and BBOX[0] <= lon <= BBOX[2]


def wiki_articles():
    return bundle()["wikipedia"]["articles"]


def wiki_clean(t):
    t = re.sub(r"<ref[^>]*/>", "", t or "")
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"'''?", "", t)
    t = t.replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", t)


def check_quote(title, phrase):
    """Assert that a phrase I rely on appears in the downloaded Wikipedia article text."""
    txt = re.sub(r"\s+", " ", wiki_clean(wiki_articles()[title]["text"]))
    ph = re.sub(r"\s+", " ", phrase)
    assert ph.lower() in txt.lower(), (title, phrase)
    return True


def wiki_url(title):
    return "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")


# ---------- countries ----------
_NAT = None
def nations():
    """List of (name, prepared shapely geometry) for England, Scotland, Wales (from ONS counties),
    Northern Ireland, Republic of Ireland and the Isle of Man (from Natural Earth 10m)."""
    global _NAT
    if _NAT is not None:
        return _NAT
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from shapely.prepared import prep
    g = json.load(open(COUNTIES))
    by = {}
    for f in g["features"]:
        by.setdefault(f["properties"]["nation"], []).append(shape(f["geometry"]).buffer(0))
    out = [(k, unary_union(v)) for k, v in by.items()]
    ne = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
    gb = unary_union([v for k, v in out])
    for f in ne["features"]:
        a3 = f["properties"].get("ADM0_A3")
        if a3 == "IRL":
            out.append(("Republic of Ireland", shape(f["geometry"]).buffer(0)))
        elif a3 == "IMN":
            out.append(("Isle of Man", shape(f["geometry"]).buffer(0)))
        elif a3 == "GBR":
            ni = shape(f["geometry"]).buffer(0).difference(gb.buffer(0.02))
            from shapely.geometry import box
            out.append(("Northern Ireland", ni.intersection(box(-8.3, 53.9, -5.3, 55.5))))
    _NAT = [(k, v, prep(v)) for k, v in out]
    return _NAT


def nation_of(lat, lon, tol=0.06):
    from shapely.geometry import Point
    p = Point(lon, lat)
    for k, g, pg in nations():
        if pg.contains(p):
            return k
    best, bd = "", 1e9
    for k, g, pg in nations():
        d = g.distance(p)
        if d < bd:
            best, bd = k, d
    return best if bd <= tol else ""


# ---------- web mercator ----------
def merc_y(lat):
    lat = np.radians(np.asarray(lat, dtype=float))
    return np.log(np.tan(np.pi / 4 + lat / 2))


def inv_merc_y(y):
    return np.degrees(2 * np.arctan(np.exp(np.asarray(y, dtype=float))) - np.pi / 2)


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return 12742 * math.asin(math.sqrt(a))


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


BAD = ("\u2014", "\u2013", "--")
def assert_clean(text, where=""):
    for b in BAD:
        assert b not in text, (where, b, text[max(0, text.find(b) - 60): text.find(b) + 60])
