"""Step 5. header.png, the 1200 x 630 social card. Run: python3 code/05_header.py"""
from figlib import *

R = json.load(open(os.path.join(DATA, "results.json")))
ev = load_ev()
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([0.5, 0.0, 0.5, 1.0]); ax.set_anchor("E")
base_map(ax, lon=(-10.9, 2.1), lat=(49.85, 58.8), shade_k=0.7, haze_alpha=0.75)
coast(ax, 0.4)
points(ax, ev, ["hillfort", "germanic", "latin", "ogham", "pictish", "christian", "royal", "dyke"], size=0.55)
kingdom_labels(ax, size=10.5, skip=("Ebrauc", "Elmet", "Pengwern", "Gwent", "Ergyng", "Glywysing", "Brycheiniog", "Lindsey", "Essex", "Alt Clut (later Strathclyde)"))
fig.text(0.045, 0.90, "DATA STUDY  ·  EARLY MEDIEVAL", family=MONO, fontsize=12, color="#8C3B2A", va="top")
fig.text(0.045, 0.80, "Britain in", fontproperties=DISP, fontsize=58, color=FG, va="top", fontweight="black")
fig.text(0.045, 0.62, "AD 500", fontproperties=DISP, fontsize=66, color="#8C3B2A", va="top", style="italic")
fig.text(0.045, 0.42, "What the ground tells us: reused hillforts,\nAnglo-Saxon graves, Latin and ogham stones,\nPictish symbols, and kingdoms we can name\nbut cannot draw.", family=SER, fontsize=15, color=FG, va="top", linespacing=1.3)
fig.text(0.045, 0.07, f"{R['n_mapped_not_roman']:,} pieces of evidence  ·  {R['kingdoms']['n']} uncertain kingdoms\nDr Tristan Hotham  ·  tristan-hotham.github.io/britain-500", family=MONO, fontsize=11.5, color=MUT, va="bottom", linespacing=1.5)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")).convert("RGB"); assert im.size == (1200, 630), im.size; im.save(os.path.join(ROOT, "header.png"), optimize=True)
print("header.png", im.size)
