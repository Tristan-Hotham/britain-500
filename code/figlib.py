"""Shared drawing helpers for the header, blog and paper figures and the collage (matplotlib, no web tiles)."""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import to_rgb
from common import *

FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    p = os.path.join(FONT_DIR, f)
    if os.path.exists(p):
        fm.fontManager.addfont(p)
DISP = fm.FontProperties(fname=os.path.join(FONT_DIR, "FrauncesVar.ttf")) if os.path.exists(os.path.join(FONT_DIR, "FrauncesVar.ttf")) else fm.FontProperties(family="serif", weight="bold")
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6B6257", "axes.labelcolor": "#2A2520", "xtick.color": "#6B6257", "ytick.color": "#6B6257", "svg.fonttype": "none"})

BG = "#F4EEE2"; FG = "#2A2520"; MUT = "#6B6257"; RULE = "#D9CFBD"; SEA = "#DCE2DF"; LAND = "#F7F2E7"; COAST = "#8F8473"
COL = {"germanic": "#B5562B", "brittonic": "#2F6F73", "irish": "#5E7A2E", "pictish": "#6C4A8A"}
LCOL = {"hillfort": "#B8862B", "germanic": "#B5562B", "latin": "#2F6F73", "ogham": "#5E7A2E", "pictish": "#6C4A8A", "christian": "#2B4470",
        "royal": "#7D1F1F", "dyke": "#7A5C3A", "roman": "#7E786E", "other": "#9A8F80"}
LNAME = {"hillfort": "Hillforts reused", "germanic": "Anglo-Saxon graves and settlements", "latin": "Latin inscribed stones", "ogham": "Ogham stones",
         "pictish": "Pictish stones", "christian": "Early churches and monasteries", "royal": "Royal and high-status sites", "dyke": "Dykes",
         "roman": "Roman towns and forts", "other": "Other early medieval sites"}


def mx(lon): return np.asarray(lon, dtype=float)
def my(lat): return merc_y(lat) * 180 / math.pi     # mercator y in "degree-like" units, so x and y scale alike


def relief_rgb(bg_land=LAND, sea=SEA, shade_k=0.55):
    """Vellum land with hill shading, sea flat, in a mercator image; returns (rgb, extent)."""
    z = np.load(os.path.join(WORK, "relief.npz"))
    meta = json.loads(str(z["meta"])); zz = meta["z"]; x0, y0 = meta["x0"], meta["y0"]
    lm = z["lm"]; sh = z["shade"].astype(np.float32)
    H, W = lm.shape
    land = np.array(to_rgb(bg_land)); sc = np.array(to_rgb(sea))
    f = 1 + shade_k * (np.nan_to_num(sh, nan=math.sin(math.radians(45))) - math.sin(math.radians(45)))
    rgb = np.where(lm[..., None], np.clip(land[None, None] * f[..., None], 0, 1), sc[None, None])
    n = 256 * 2 ** zz
    lon0 = x0 / n * 360 - 180; lon1 = (x0 + W) / n * 360 - 180
    yt = (1 - 2 * y0 / n) * 180; yb = (1 - 2 * (y0 + H) / n) * 180
    return rgb, (lon0, lon1, yb, yt), lm


def haze_rgba(c, alpha=0.75):
    """A culture density grid as an RGBA image (same frame as the page overlay)."""
    G = np.load(os.path.join(WORK, "grids.npz"))
    meta = json.loads(str(G["meta"])); g = G[c]; zz = meta["z"]
    ref = np.percentile(g[g > 0], 99); a = np.clip(g / ref, 0, 1) ** 0.65; a[a < 0.06] = 0
    H, W = g.shape; n = 256 * 2 ** zz
    im = np.zeros((H, W, 4)); im[..., :3] = to_rgb(COL[c]); im[..., 3] = a * alpha
    lon0 = meta["x0"] / n * 360 - 180; lon1 = (meta["x0"] + W) / n * 360 - 180
    yt = (1 - 2 * meta["y0"] / n) * 180; yb = (1 - 2 * (meta["y0"] + H) / n) * 180
    return im, (lon0, lon1, yb, yt)


def load_ev():
    ev = read_csv(os.path.join(DATA, "evidence.csv"))
    for r in ev:
        r["lat"] = float(r["lat"]); r["lon"] = float(r["lon"]); r["d0"] = int(r["d0"]); r["d1"] = int(r["d1"])
    return ev


def base_map(ax, lon=(-10.6, 1.9), lat=(49.9, 58.8), shade_k=0.6, haze=True, haze_alpha=0.7, land=LAND, sea=SEA):
    rgb, ext, lm = relief_rgb(land, sea, shade_k)
    ax.imshow(rgb, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
    if haze:
        for c in ("irish", "pictish", "brittonic", "germanic"):
            im, e2 = haze_rgba(c, haze_alpha)
            ax.imshow(im, extent=e2, origin="upper", interpolation="bilinear", zorder=1)
    ax.set_xlim(*lon); ax.set_ylim(my(lat[0]), my(lat[1]))
    ax.set_aspect("equal"); ax.axis("off")


def coast(ax, lw=0.5, color=COAST):
    gj = json.load(open(os.path.join(DATA, "land.json")))
    for g in gj:
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                a = np.array(ring)
                ax.plot(a[:, 0], my(a[:, 1]), color=color, lw=lw, zorder=2)


def points(ax, ev, layers, size=1.0, year=None, edge=None):
    order = ["roman", "other", "ogham", "latin", "pictish", "germanic", "christian", "hillfort", "dyke", "royal"]
    for L in order:
        if L not in layers: continue
        rs = [r for r in ev if r["layer"] == L and (year is None or r["d0"] <= year <= r["d1"])]
        if not rs: continue
        x = [r["lon"] for r in rs]; y = my([r["lat"] for r in rs])
        site = np.array([r["dq"] == "site" for r in rs])
        s = {"royal": 70, "hillfort": 26, "dyke": 30}.get(L, 16) * size
        c = LCOL[L]
        if L == "royal":
            ax.scatter(x, y, s=s, c=c, edgecolors=FG if edge is None else edge, linewidths=1.2, zorder=6)
            continue
        x = np.array(x); y = np.array(y)
        if site.any():
            ax.scatter(x[site], y[site], s=s, c=c, edgecolors="white" if edge is None else edge, linewidths=0.4, zorder=5)
        if (~site).any():
            ax.scatter(x[~site], y[~site], s=s, facecolors="none", edgecolors=c, linewidths=1.0, zorder=4, alpha=0.95)


# label positions moved slightly in static figures so that neighbouring names do not collide (the zones are unchanged)
NUDGE = {"Elmet": (-1.65, 53.7), "Ebrauc": (-1.15, 54.18), "Deira": (-0.3, 54.0), "Pengwern": (-2.3, 52.9), "Powys": (-3.35, 52.62),
         "Ergyng": (-2.4, 51.98), "Brycheiniog": (-3.6, 52.0), "Gwent": (-2.55, 51.7), "Glywysing": (-3.55, 51.52),
         "Alt Clut": (-4.25, 55.78), "Dál Riata": (-5.75, 56.2)}


def kingdom_labels(ax, size=13, stroke=LAND, skip=()):
    import matplotlib.patheffects as pe
    K = read_csv(os.path.join(DATA, "kingdoms.csv"))
    for k in K:
        if k["name"] in skip: continue
        nm = k["name"].split(" (")[0]
        lo, la = NUDGE.get(nm, (float(k["lon"]), float(k["lat"])))
        t = ax.text(lo, my(la), nm, family=SER, style="italic", fontsize=size * (0.82 if float(k["r_km"]) < 30 else 1),
                    color=COL[k["group"]], ha="center", va="center", zorder=8)
        t.set_path_effects([pe.withStroke(linewidth=3, foreground=stroke)])


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    from PIL import Image
    im = Image.open(path); im = im.convert("RGB") if im.mode == "RGBA" else im
    im.save(path, optimize=True)
