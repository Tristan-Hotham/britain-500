"""Step 6. Static figures for the blog (release/blog/b_*.png, 1520 px wide) and the paper (release/paper/fig_*.png).
Run: python3 code/06_figures.py"""
import shutil
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from figlib import *

R = json.load(open(os.path.join(DATA, "results.json")))
ev = load_ev()
OUT = os.path.join(ROOT, "release", "blog"); os.makedirs(OUT, exist_ok=True)
POUT = os.path.join(ROOT, "release", "paper"); os.makedirs(POUT, exist_ok=True)
W = 15.2   # inches at dpi 100 = 1520 px
DPI = 100


def finish(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=DPI, facecolor=BG)
    plt.close(fig)
    from PIL import Image
    im = Image.open(p).convert("RGB"); im.save(p, optimize=True)
    shutil.copy(p, os.path.join(POUT, "fig_" + name[2:]))
    print(name, im.size)


def legend_handles(layers):
    h = []
    for L in layers:
        if L == "royal":
            h.append(Line2D([], [], marker="o", ls="", markersize=11, markerfacecolor=LCOL[L], markeredgecolor=FG, label=LNAME[L]))
        else:
            h.append(Line2D([], [], marker="o", ls="", markersize=8, markerfacecolor=LCOL[L], markeredgecolor="white", label=LNAME[L]))
    h.append(Line2D([], [], marker="o", ls="", markersize=8, markerfacecolor="none", markeredgecolor=MUT, label="Hollow: dated only by type"))
    return h


# ---------- 1. the big map
fig = plt.figure(figsize=(W, 19.0), facecolor=BG)
ax = fig.add_axes([0.0, 0.085, 1.0, 0.915])
base_map(ax, lon=(-10.7, 2.0), lat=(49.85, 58.75), shade_k=0.75, haze_alpha=0.72)
coast(ax, 0.6)
LAYS = ["hillfort", "germanic", "latin", "ogham", "pictish", "christian", "royal", "dyke"]
points(ax, ev, LAYS, size=1.6)
kingdom_labels(ax, size=19)
lx = fig.add_axes([0.03, 0.015, 0.94, 0.07]); lx.axis("off")
lx.legend(handles=legend_handles(LAYS), loc="center", ncol=3, frameon=False, fontsize=14, handletextpad=0.4, columnspacing=1.6)
fig.text(0.5, 0.003, "Haze: kernel density of the evidence for each tradition (20 km kernel). Italic names: approximate kingdom zones, not borders.",
         family=MONO, fontsize=12, color=MUT, ha="center", va="bottom")
finish(fig, "b_map.png")

# ---------- 2. longitude profile
P = R["profile"]
fig, ax = plt.subplots(figsize=(W, 7.2), facecolor=BG); ax.set_facecolor(BG)
x = np.array([p["lon_from"] + 0.25 for p in P])
ax.bar(x - 0.11, [p["brittonic"] for p in P], width=0.2, color=COL["brittonic"], label="Latin inscribed stones and British high-status sites")
ax.bar(x + 0.11, [p["germanic"] for p in P], width=0.2, color=COL["germanic"], label="Anglo-Saxon cemeteries, burials and settlements")
ax.set_xticks(np.arange(-6, 2.01, 1)); ax.set_xticklabels([f"{abs(int(v))}°W" if v < 0 else ("0°" if v == 0 else f"{int(v)}°E") for v in np.arange(-6, 2.01, 1)], fontsize=15)
ax.tick_params(axis="y", labelsize=14)
ax.set_ylabel("Sites in each half-degree strip", fontsize=15)
ax.set_xlabel("Longitude (Great Britain south of the Forth)", fontsize=15)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.axvline(R["eastwest"]["germanic_median_lon"], color=COL["germanic"], ls=":", lw=2)
ax.axvline(R["eastwest"]["brittonic_median_lon"], color=COL["brittonic"], ls=":", lw=2)
ax.text(R["eastwest"]["germanic_median_lon"] - 0.05, ax.get_ylim()[1] * 0.6, "median", color=COL["germanic"], fontsize=13, ha="right")
ax.text(R["eastwest"]["brittonic_median_lon"] - 0.05, ax.get_ylim()[1] * 0.6, "median", color=COL["brittonic"], fontsize=13, ha="right")
ax.legend(frameon=False, fontsize=14, loc="upper center", bbox_to_anchor=(0.62, 0.86))
fig.tight_layout()
finish(fig, "b_profile.png")

# ---------- 3. hillforts
H = R["hill"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 7.6), facecolor=BG, gridspec_kw={"width_ratios": [1.25, 1]})
rows = sorted(H["by_country"].items(), key=lambda kv: kv[1]["share"])
a1.barh([k for k, v in rows], [100 * v["share"] for k, v in rows], color=LCOL["hillfort"])
for i, (k, v) in enumerate(rows):
    a1.text(100 * v["share"] + 0.8, i, f"{v['dated']} of {v['n']:,}", va="center", fontsize=13.5, color=MUT)
a1.set_xlim(0, 60); a1.set_xlabel("Share with dating evidence for AD 400 to 800 (%)", fontsize=14)
a1.tick_params(labelsize=14)
cats = ["On the coast", "Promontory fort"]
reused = [100 * H["coastal_share"], 100 * H["promontory_share"]]; allf = [100 * H["coastal_all_share"], 100 * H["promontory_all_share"]]
y = np.arange(2)
a2.barh(y + 0.2, reused, height=0.38, color=LCOL["hillfort"], label=f"Reused, AD 400 to 800 ({H['dated']})")
a2.barh(y - 0.2, allf, height=0.38, color="#CDBFA6", label=f"All Atlas hillforts ({H['atlas_total']:,})")
for i in range(2):
    a2.text(reused[i] + 1, i + 0.2, f"{reused[i]:.0f}%", va="center", fontsize=14)
    a2.text(allf[i] + 1, i - 0.2, f"{allf[i]:.0f}%", va="center", fontsize=14, color=MUT)
a2.set_yticks(y); a2.set_yticklabels(cats, fontsize=14); a2.set_xlim(0, 55); a2.set_xlabel("% of hillforts", fontsize=14)
a2.legend(frameon=False, fontsize=13, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1)
for a in (a1, a2):
    a.set_facecolor(BG)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    a.tick_params(axis="x", labelsize=13)
fig.tight_layout(w_pad=4)
finish(fig, "b_hillforts.png")

# ---------- 4. the Irish Sea
fig = plt.figure(figsize=(W, 15.5), facecolor=BG)
ax = fig.add_axes([0, 0.06, 1, 0.94])
base_map(ax, lon=(-10.6, -2.4), lat=(50.6, 56.6), shade_k=0.8, haze_alpha=0.6)
coast(ax, 0.7)
points(ax, ev, ["ogham", "latin", "hillfort", "royal", "christian"], size=2.2)
K = {k["name"]: k for k in read_csv(os.path.join(DATA, "kingdoms.csv"))}
for nm in ("Dyfed", "Gwynedd", "Brycheiniog", "Dumnonia", "Dál Riata", "Alt Clut (later Strathclyde)", "Rheged", "Glywysing"):
    k = K[nm]; lo, la = NUDGE.get(nm.split(" (")[0], (float(k["lon"]), float(k["lat"])))
    t = ax.text(lo, my(la), nm.split(" (")[0], family=SER, style="italic", fontsize=24, color=COL[k["group"]], ha="center", va="center", zorder=9)
    t.set_path_effects([pe.withStroke(linewidth=4, foreground=LAND)])
roy = {r["name"]: r for r in ev if r["layer"] == "royal"}
for nm, dx, dy in [("Dunadd", 0.25, 0.25), ("Dumbarton Rock (Alt Clut)", 0.25, -0.35), ("Dinas Powys", 0.3, -0.25), ("Tintagel", 0.3, 0.2)]:
    r = roy[nm]
    ax.annotate(nm.split(" (")[0], (r["lon"], my(r["lat"])), (r["lon"] + dx, my(r["lat"]) + dy * 1.6), fontsize=15, family=MONO, color=FG,
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.8), zorder=10, path_effects=[pe.withStroke(linewidth=3, foreground=LAND)])
lx = fig.add_axes([0.03, 0.0, 0.94, 0.055]); lx.axis("off")
lx.legend(handles=legend_handles(["ogham", "latin", "hillfort", "christian", "royal"]), loc="center", ncol=3, frameon=False, fontsize=14)
finish(fig, "b_irishsea.png")

# ---------- 5. kingdoms: evidence in each zone
Z = R["kingdoms"]["zones"]
order = {"brittonic": 0, "irish": 1, "pictish": 2, "germanic": 3}
Z = sorted(Z, key=lambda z: (order[z["group"]], z["n"]))
fig, ax = plt.subplots(figsize=(W, 11.5), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(Z)); left = np.zeros(len(Z))
for c, lab in [("germanic", "Anglo-Saxon"), ("brittonic", "British"), ("irish", "Irish"), ("pictish", "Pictish"), ("untyped", "No cultural label (hillforts, churches, dykes)")]:
    v = np.array([z[c] for z in Z])
    ax.barh(y, v, left=left, color=COL.get(c, "#CDBFA6"), label=lab, height=0.7)
    left += v
ax.set_yticks(y); ax.set_yticklabels([z["name"] for z in Z], fontsize=13.5)
for t, z in zip(ax.get_yticklabels(), Z): t.set_color(COL[z["group"]]); t.set_fontstyle("italic"); t.set_family(SER); t.set_fontsize(16)
for i, z in enumerate(Z): ax.text(left[i] + 0.6, i, str(z["n"]), va="center", fontsize=13, color=MUT)
ax.set_xlabel("Pieces of evidence within the zone radius", fontsize=14); ax.tick_params(axis="x", labelsize=13)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=13, loc="lower right")
fig.tight_layout()
finish(fig, "b_kingdoms.png")

# ---------- 6. sources against the period
fig, ax = plt.subplots(figsize=(W, 6.6), facecolor=BG); ax.set_facecolor(BG)
SRC = [("Gildas, De Excidio", 480, 545), ("Bede, Ecclesiastical History", 731, 731), ("Historia Brittonum", 800, 830),
       ("Anglo-Saxon Chronicle manuscripts", 850, 1150), ("Y Gododdin, Book of Aneirin", 1250, 1300)]
ax.axvspan(450, 550, color="#8C3B2A", alpha=0.12, lw=0)
ax.text(500, len(SRC) - 0.35, "AD 450 to 550", ha="center", fontsize=13, color="#8C3B2A")
for i, (nm, a, b) in enumerate(SRC[::-1]):
    ax.barh(i, max(b - a, 6), left=a, color=FG, height=0.45)
    ax.text(max(b, a + 6) + 12, i, nm, va="center", fontsize=14)
ax.set_xlim(380, 1600); ax.set_yticks([]); ax.set_ylim(-0.6, len(SRC) - 0.1)
ax.set_xticks(range(400, 1401, 100)); ax.tick_params(labelsize=13)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.set_xlabel("Year AD: when each text was written, or (Chronicle, Gododdin) its surviving manuscripts", fontsize=13)
fig.tight_layout()
finish(fig, "b_sources.png")
