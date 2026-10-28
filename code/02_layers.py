"""Step 2. Map layers for the page and figures.

Writes (all in web-mercator rasters over the frame BBOX, or simplified vectors):
  data/land.json        Natural Earth 10m land, clipped and simplified (public domain)
  data/borders.json     modern borders for orientation (ONS nations for Great Britain, Natural Earth for Ireland)
  data/hills.png        hill shading as black and white with transparency (AWS Terrain Tiles)
  data/lowland.png      land under 5 m above sea level today (rough guide to marsh and fen in AD 500)
  data/dens_<culture>.png  kernel density of the evidence for each culture (Germanic, Brittonic, Irish, Pictish)
  data/roads.json       Roman roads (Itiner-e, Britain), simplified
  data/places.json      modern places for search and labels (OS Open Names; GeoNames for Ireland and the Isle of Man)
  work/grids.npz        the density grids and land mask, for the analysis and figures
Run: python3 code/02_layers.py
"""
import csv, io, json, math, os, zipfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from common import *

lon0, lat0, lon1, lat1 = BBOX
def gx(lon, z): return (np.asarray(lon) + 180.0) / 360.0 * 256 * 2 ** z
def gy(lat, z): return (1 - merc_y(lat) / math.pi) / 2 * 256 * 2 ** z

def frame(z):
    x0, x1 = gx(lon0, z), gx(lon1, z); y0, y1 = gy(lat1, z), gy(lat0, z)
    return x0, y0, int(round(x1 - x0)), int(round(y1 - y0))

def rnd(geom, nd=3):
    def r(c):
        if isinstance(c[0], (list, tuple)):
            return [r(x) for x in c]
        return [round(c[0], nd), round(c[1], nd)]
    g = mapping(geom); return {"type": g["type"], "coordinates": r(g["coordinates"])}

# ---------------- land, clipped and simplified
fr = box(lon0 - 7, lat0 - 4.5, lon1 + 7, lat1 + 4)   # wide, so the clipping edges stay out of view
ne = json.load(open(os.path.join(NE, "ne_10m_land.geojson")))
land = unary_union([shape(f["geometry"]).intersection(fr) for f in ne["features"] if shape(f["geometry"]).intersects(fr)])
landS = land.simplify(0.004, preserve_topology=True)
polys = [p for p in getattr(landS, "geoms", [landS]) if p.area > 0.0004]
json.dump([rnd(p) for p in polys], open(os.path.join(DATA, "land.json"), "w"), separators=(",", ":"))

# ---------------- modern borders (nation lines only, not coasts)
nat = nations()
lines = []
for i in range(len(nat)):
    for j in range(i + 1, len(nat)):
        a, b = nat[i][1], nat[j][1]
        if a.distance(b) < 0.03:
            sh = a.buffer(0.012).intersection(b.buffer(0.012))
            if sh.is_empty: continue
            ln = a.boundary.intersection(b.buffer(0.015))
            if ln.length > 0.05:
                lines.append(rnd(ln.simplify(0.004), 3))
json.dump(lines, open(os.path.join(DATA, "borders.json"), "w"), separators=(",", ":"))

# ---------------- raster frame for land mask
def land_mask(z):
    X0, Y0, W, H = frame(z)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    for p in getattr(land, "geoms", [land]):
        for ring, val in [(p.exterior, 255)] + [(r, 0) for r in p.interiors]:
            xs, ys = ring.coords.xy
            pts = list(zip(gx(np.array(xs), z) - X0, gy(np.array(ys), z) - Y0))
            if len(pts) > 2: dr.polygon(pts, fill=val)
    return np.asarray(im) > 127

# ---------------- hills and lowland at zoom 8
from dem import DEM
dem = DEM()
Z = 8
X0, Y0, W, H = frame(Z)
s = 2 ** (10 - Z)           # z10 pixels per z8 pixel
# average elevation over each z8 pixel from a 2 x 2 sample of z10 positions
el = np.zeros((H, W), np.float32)
jj, ii = np.mgrid[0:H, 0:W]
for dy in (0.25, 0.75):
    for dx in (0.25, 0.75):
        el += dem.bilinear((X0 + ii + dx) * s, (Y0 + jj + dy) * s) / 4
lm = land_mask(Z)
el[~lm] = np.minimum(el[~lm], 0)
# metres per pixel varies with latitude in mercator
lat_rows = inv_merc_y((1 - 2 * (Y0 + np.arange(H) + .5) / (256 * 2 ** Z)) * math.pi)
mpp = 2 * math.pi * 6378137 / (256 * 2 ** Z) * np.cos(np.radians(lat_rows))[:, None]
dzdy, dzdx = np.gradient(el.astype(np.float64))
dzdx /= mpp; dzdy /= mpp
ex = 2.2
slope = np.arctan(ex * np.hypot(dzdx, dzdy)); aspect = np.arctan2(-dzdx, dzdy)
az, alt = math.radians(315), math.radians(45)
shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect - math.pi / 2)
flat = math.sin(alt)
d = shade - flat
rgba = np.zeros((H, W, 4), np.uint8)
dark = d < 0
a = np.clip(np.where(dark, -d / 0.55, d / 0.35), 0, 1)
a = np.round(a * 20) / 20     # quantise for a smaller file
rgba[..., 0:3] = np.where(dark[..., None], 0, 255)
rgba[..., 3] = (a * np.where(dark, 200, 150) * lm).astype(np.uint8)
Image.fromarray(rgba, "RGBA").save(os.path.join(DATA, "hills.png"), optimize=True)
low = lm & (el <= 5)
low = ndimage.binary_opening(low, iterations=1)
lo = np.zeros((H, W, 4), np.uint8); lo[low] = (60, 120, 140, 255)
Image.fromarray(lo, "RGBA").save(os.path.join(DATA, "lowland.png"), optimize=True)
grid_meta = {"z": Z, "x0": X0, "y0": Y0, "w": W, "h": H}
print("hills", W, H, os.path.getsize(os.path.join(DATA, "hills.png")) // 1024, "KB; lowland km2 approx",
      int((low * (mpp / 1000) ** 2).sum()))
low_km2 = float((low * (mpp / 1000) ** 2).sum())
# keep a 1:4 elevation grid for figures
np.savez_compressed(os.path.join(WORK, "relief.npz"), el=el[::2, ::2].astype(np.int16), lm=lm[::2, ::2], shade=shade[::2, ::2].astype(np.float16), meta=json.dumps({"z": Z - 1, "x0": X0 / 2, "y0": Y0 / 2}))
del el, dzdx, dzdy, slope, aspect, shade, rgba, a, jj, ii

# ---------------- culture densities at zoom 6 (Gaussian kernel, sigma 20 km)
ev = read_csv(os.path.join(DATA, "evidence.csv"))
CUL = {"germanic": "#B5562B", "brittonic": "#2F6F73", "irish": "#5E7A2E", "pictish": "#6C4A8A"}
ZK = 6
KX0, KY0, KW, KH = frame(ZK)
klm = land_mask(ZK)
klat = inv_merc_y((1 - 2 * (KY0 + np.arange(KH) + .5) / (256 * 2 ** ZK)) * math.pi)
kmpp = 2 * math.pi * 6378137 / (256 * 2 ** ZK) * np.cos(np.radians(klat))
SIG_KM = 20.0
grids = {}
for c in CUL:
    pts = [r for r in ev if r["culture"] == c and r["layer"] != "roman"]
    g = np.zeros((KH, KW))
    for r in pts:
        x = int(gx(float(r["lon"]), ZK) - KX0); y = int(gy(float(r["lat"]), ZK) - KY0)
        if 0 <= x < KW and 0 <= y < KH: g[y, x] += 1
    # sigma in pixels depends on latitude: blur in bands
    out = np.zeros_like(g)
    for y0 in range(0, KH, 40):
        sl = slice(max(0, y0 - 120), min(KH, y0 + 160))
        sg = SIG_KM * 1000 / kmpp[min(KH - 1, y0 + 20)]
        b = ndimage.gaussian_filter(g[sl], sg, mode="constant")
        out[y0:y0 + 40] = b[y0 - sl.start: y0 - sl.start + 40]
    out *= klm
    grids[c] = out
    ref = np.percentile(out[out > 0], 99) if (out > 0).any() else 1
    al = np.clip(out / ref, 0, 1) ** 0.65
    al[al < 0.06] = 0
    col = tuple(int(CUL[c][i:i + 2], 16) for i in (1, 3, 5))
    im = np.zeros((KH, KW, 4), np.uint8); im[..., 0], im[..., 1], im[..., 2] = col
    im[..., 3] = (al * 235).astype(np.uint8)
    Image.fromarray(im, "RGBA").save(os.path.join(DATA, f"dens_{c}.png"), optimize=True)
    print(c, len(pts), "points")
np.savez_compressed(os.path.join(WORK, "grids.npz"), **{k: v.astype(np.float32) for k, v in grids.items()}, lm=klm,
                    meta=json.dumps({"z": ZK, "x0": KX0, "y0": KY0, "w": KW, "h": KH, "sigma_km": SIG_KM}))

# ---------------- Roman roads (Itiner-e), simplified
rd = json.load(open(ITINERE))
rl = []
for f in rd["features"]:
    g = shape(f["geometry"]).simplify(0.003)
    if g.is_empty: continue
    rl.append(rnd(g, 3))
json.dump(rl, open(os.path.join(DATA, "roads.json"), "w"), separators=(",", ":"))
print("roads", len(rl), os.path.getsize(os.path.join(DATA, "roads.json")) // 1024, "KB")

# ---------------- places for search and labels
pl = []
seen = set()
RANK = {"City": 3, "Town": 2, "Village": 1}
with open(OSNAMES, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rk = RANK.get(r["local_type"])
        if not rk: continue
        nm, alt = r["name1"], r["name2"]
        if alt and r["lang1"] in ("cym", "gla") and r["lang2"] == "eng":
            nm, alt = alt, nm          # English name on the map; the Welsh or Gaelic name stays searchable
        area = r["county"] or r["district"] or r["region"]
        key = (nm, area)
        if key in seen: continue
        seen.add(key)
        pl.append([nm, area, round(float(r["lat"]), 4), round(float(r["lon"]), 4), rk])
        if alt:
            pl.append([alt, area, round(float(r["lat"]), 4), round(float(r["lon"]), 4), 0])
n_gb = len(pl)
z = zipfile.ZipFile(CITIES)
cc_name = {"IE": "Ireland", "IM": "Isle of Man"}
for line in io.TextIOWrapper(z.open("cities1000.txt"), encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    cc = p[8]; adm = p[10]
    if cc in ("IE", "IM") or (cc == "GB" and adm == "NIR"):
        popn = int(p[14] or 0)
        rk = 3 if popn >= 100000 else 2 if popn >= 5000 else 1
        pl.append([p[1], cc_name.get(cc, "Northern Ireland"), round(float(p[4]), 4), round(float(p[5]), 4), rk])
json.dump(pl, open(os.path.join(DATA, "places.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("places", n_gb, len(pl) - n_gb, os.path.getsize(os.path.join(DATA, "places.json")) // 1024, "KB")
json.dump({"hills": grid_meta, "dens": {"z": ZK, "x0": KX0, "y0": KY0, "w": KW, "h": KH, "sigma_km": SIG_KM},
           "lowland_km2": low_km2, "places_gb": n_gb, "places_other": len(pl) - n_gb, "colours": CUL},
          open(os.path.join(WORK, "layers_meta.json"), "w"))
