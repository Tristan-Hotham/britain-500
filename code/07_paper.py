"""Step 7. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Britain_in_AD_500.tex and compile it with xelatex (figures from step 6).
Run: python3 code/07_paper.py
"""
import importlib.util, json, os, re, shutil, subprocess
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Britain_in_AD_500"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")

LN = {"hillfort": "Hillforts with dating evidence, AD 400 to 800", "germanic": "Anglo-Saxon cemeteries, burials, settlements", "latin": "Latin inscribed stones",
      "ogham": "Ogham find-spots", "pictish": "Pictish stones", "christian": "Early churches and monasteries", "royal": "High-status sites (hand list)",
      "dyke": "Dykes (hand list)", "other": "Other early medieval sites", "roman": "Roman towns and forts (context)"}
SRC = {"hillfort": "Atlas of Hillforts", "germanic": "Wikidata", "latin": "Wikidata", "ogham": "Wikidata, Ireland SMR", "pictish": "Wikidata", "christian": "Wikidata",
       "royal": "Wikipedia", "dyke": "Wikipedia, Wikidata", "other": "Wikidata", "roman": "Pleiades"}
DAT = {"hillfort": "Atlas band", "germanic": "type, 450 to 650", "latin": "type, 400 to 700", "ogham": "type, 400 to 600", "pictish": "type, 500 to 850",
       "christian": "start date or type", "royal": "Wikipedia text", "dyke": "Wikipedia text", "other": "type", "roman": "Pleiades periods"}
rows = ""
for L in ["hillfort", "germanic", "latin", "ogham", "pictish", "christian", "royal", "dyke", "other", "roman"]:
    nat = sorted(R["layer_nation"][L].items(), key=lambda kv: -kv[1])[:3]
    rows += f"{LN[L]} & {R['layers'][L]:,} & {tex(', '.join(f'{k} {v}' for k, v in nat))} & {SRC[L]} & {DAT[L]}\\\\\n"
T_LAYERS = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The evidence layers: counts, the three countries with most entries, source and how each is dated.}\\label{tab:layers}"
            "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{4.6cm}r>{\\raggedright\\arraybackslash}p{4.2cm}>{\\raggedright\\arraybackslash}p{2.4cm}>{\\raggedright\\arraybackslash}p{2.3cm}}\\toprule Layer & Mapped & Main countries & Source & Dating\\\\\\midrule\n"
            + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(k)} & {v['n']:,} & {v['dated']} & {100 * v['share']:.1f}\\%\\\\\n" for k, v in sorted(R["hill"]["by_country"].items(), key=lambda kv: -kv[1]["dated"]))
rows += f"\\midrule All & {R['hill']['atlas_total']:,} & {R['hill']['dated']} & {100 * R['hill']['share']:.1f}\\%\\\\\n"
T_HILL = ("\\begin{table}[tbp]\\centering\\small\\caption{Atlas hillforts with dating evidence for AD 400 to 800, by country.}\\label{tab:hill}"
          "\\begin{tabular}{lrrr}\\toprule Country & Hillforts & Dated AD 400 to 800 & Share\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
K = {k["name"]: k for k in read_csv(os.path.join(DATA, "kingdoms.csv"))}
GN = {"brittonic": "British", "germanic": "Anglo-Saxon", "irish": "Gaelic", "pictish": "Pictish"}
order = {"brittonic": 0, "irish": 1, "pictish": 2, "germanic": 3}
rows = ""
for z in sorted(R["kingdoms"]["zones"], key=lambda z: (order[z["group"]], -z["n"])):
    m = "" if z["matching_share"] is None else f"{100 * z['matching_share']:.0f}\\%"
    rows += f"{tex(z['name'])} & {GN[z['group']]} & {tex(K[z['name']]['first_written'])} & {z['n']} & {m}\\\\\n"
T_K = ("\\begin{table}[p]\\centering\\scriptsize\\caption{Kingdoms on the map: earliest written mention (summarised from Wikipedia), evidence within the zone radius, and the share of culturally labelled evidence in the zone that matches the kingdom's tradition.}\\label{tab:kingdoms}"
       "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{2.6cm}l>{\\raggedright\\arraybackslash}p{8.6cm}rr}\\toprule Kingdom & Tradition & First written mention & Evidence & Match\\\\\\midrule\n"
       + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tex(b.fmt(b.get(m.group(1)), m.group(3))), t)
t = t.replace("{{TABLE_LAYERS}}", T_LAYERS).replace("{{TABLE_HILL}}", T_HILL).replace("{{TABLE_KINGDOMS}}", T_K)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print("overfull:", log.count("Overfull"), "missing chars:", log.count("Missing character"))
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
assert_clean(txt, "paper pdf")
print("paper written", r.returncode, len(txt.split()), "words")
