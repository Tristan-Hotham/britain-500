"""r/dataisbeautiful collage for Britain in AD 500 (2400 x 3000 px). Run from the project folder: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib.patheffects as pe
from figlib import *

R = json.load(open(os.path.join(DATA, "results.json")))
ev = load_ev()
PAPER = "#F1EAD8"; RED = "#8C3B2A"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=PAPER)

fig.text(0.045, 0.972, "Who held Britain in AD 500?", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.045, 0.915, f"Popular maps draw neat kingdoms. Almost nothing was written at the time, so I mapped what the ground can place:\n"
         f"{R['n_mapped_not_roman']:,} pieces of evidence for the years around 500, with the kingdom names laid on top as uncertain zones.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# big map
ax = fig.add_axes([0.0, 0.265, 0.62, 0.62])
base_map(ax, lon=(-10.7, 2.0), lat=(49.85, 58.75), shade_k=0.75, haze_alpha=0.75, land="#F8F3E8", sea="#DDE3DF")
coast(ax, 0.45)
points(ax, ev, ["hillfort", "germanic", "latin", "ogham", "pictish", "christian", "royal", "dyke"], size=0.6)
kingdom_labels(ax, size=11.5, stroke="#F8F3E8", skip=("Ebrauc", "Pengwern", "Ergyng", "Gwent", "Glywysing", "Brycheiniog", "Elmet", "Essex"))
roy = {r["name"]: r for r in ev if r["layer"] == "royal"}
for nm, lab, dx, dy in [("Tintagel", "Tintagel\npalace, 5th or 6th c.", -3.0, -0.5), ("Dunadd", "Dunadd\nseat of Dál Riata", -2.6, 0.9), ("Sutton Hoo", "Sutton Hoo\nship burial", -1.0, 2.6)]:
    r = roy[nm]
    ax.annotate(lab, (r["lon"], my(r["lat"])), (r["lon"] + dx, my(r["lat"]) + dy), family=MONO, fontsize=9.5, color=FG, ha="left",
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.7), path_effects=[pe.withStroke(linewidth=3, foreground=PAPER)], zorder=12)

# headline numbers
E = R["eastwest"]; H = R["hill"]
items = [(f"{abs(E['brittonic_median_lon']):.2f}°W vs {abs(E['germanic_median_lon']):.2f}°W",
          f"median longitude of western inscribed stones\nand of Anglo-Saxon graves. Just {E['brit_within_50km_of_ger']} of {E['brittonic_n']}\nwestern sites has a Saxon site within 50 km."),
         (f"{H['dated']} of {H['atlas_total']:,}", f"hillforts have dating evidence for AD 400 to 800.\n{100 * H['coastal_share']:.0f}% of them are on the coast, against\n{100 * H['coastal_all_share']:.0f}% of all hillforts."),
         (f"{100 * R['ogham']['ireland_share']:.0f}%", f"of {R['ogham']['spots']} ogham find-spots are in Ireland;\n{100 * R['latin']['wales_share']:.0f}% of {R['latin']['n']} Latin-inscribed stones\nare in Wales."),
         (f"{R['kingdoms']['n']}", "kingdoms we can name, mostly from texts\nwritten centuries later. None has a border\nwe can draw.")]
y = 0.865
for big, small in items:
    fig.text(0.63, y, big, fontproperties=DISP, fontsize=30 if len(big) > 8 else 38, color=RED, va="top")
    fig.text(0.63, y - 0.045, small, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.4)
    y -= 0.152

# legend
from matplotlib.lines import Line2D
h = [Line2D([], [], marker="o", ls="", ms=7, mfc=LCOL[k], mec="white", label=LNAME[k]) for k in ("hillfort", "germanic", "latin", "ogham", "pictish", "christian")]
h.append(Line2D([], [], marker="o", ls="", ms=9, mfc=LCOL["royal"], mec=FG, label="High-status sites"))
h.append(Line2D([], [], marker="o", ls="", ms=7, mfc="none", mec=MUT, label="Hollow: dated only by type"))
lx = fig.add_axes([0.03, 0.245, 0.94, 0.035]); lx.axis("off")
lx.legend(handles=h, ncol=4, loc="center", frameon=False, fontsize=9.5, columnspacing=1.2, handletextpad=0.3)

# small multiples: one tradition each
fig.text(0.045, 0.233, "FOUR HABITS, FOUR CORNERS  ·  each tradition's evidence and its smoothed density", family=MONO, fontsize=11, color=MUT)
SM = [("germanic", ["germanic"], "Anglo-Saxon graves"), ("brittonic", ["latin"], "Latin inscribed stones"), ("irish", ["ogham"], "Ogham stones"), ("pictish", ["pictish"], "Pictish stones")]
for i, (c, lays, lab) in enumerate(SM):
    a = fig.add_axes([0.01 + i * 0.245, 0.06, 0.235, 0.145])
    rgb, ext, lm = relief_rgb("#E7DFCC", PAPER, 0.0)
    a.imshow(rgb, extent=ext, origin="upper", zorder=0)
    im, e2 = haze_rgba(c, 0.85); a.imshow(im, extent=e2, origin="upper", interpolation="bilinear", zorder=1)
    rs = [r for r in ev if r["layer"] in lays]
    a.scatter([r["lon"] for r in rs], my([r["lat"] for r in rs]), s=2.2, c=COL[c], zorder=3)
    a.set_xlim(-10.6, 2.0); a.set_ylim(my(49.9), my(58.7)); a.set_aspect("equal"); a.axis("off")
    a.set_title(f"{lab}\n{len(rs):,}", family=MONO, fontsize=11, color=FG, pad=2)

fig.text(0.045, 0.012, "Data: Atlas of Hillforts of Britain and Ireland (Lock and Ralston 2017, CC BY-SA 4.0); Wikidata (CC0); Ireland Sites and Monuments Record (CC BY 4.0);\n"
         "Pleiades (CC BY 3.0); Wikipedia (CC BY-SA 4.0); AWS Terrain Tiles; Natural Earth. Kingdom names: approximate zones from Wikipedia, not borders.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib. Interactive: tristan-hotham.github.io/britain-500",
         family=MONO, fontsize=8.6, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(ROOT, "reddit", "britain_in_ad_500.png")
fig.savefig(out, dpi=200, facecolor=PAPER); plt.close(fig)
from PIL import Image
im = Image.open(out).convert("RGB"); assert im.size == (2400, 3000), im.size; im.save(out, optimize=True)
print(out, im.size)
