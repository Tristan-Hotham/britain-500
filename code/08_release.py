"""Step 8. Blog post and metadata (release/blog/), Zenodo files and metadata (release/zenodo/).
Run: python3 code/08_release.py"""
import importlib.util, json, os, re, shutil, zipfile
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
REL = os.path.join(ROOT, "release"); BL = os.path.join(REL, "blog"); ZE = os.path.join(REL, "zenodo")
os.makedirs(BL, exist_ok=True); os.makedirs(ZE, exist_ok=True)
NAME = "Hotham_Britain_in_AD_500"

# ---- README from its template
rd = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: b.fmt(b.get(m.group(1)), m.group(3)), open(os.path.join(HERE, "readme_template.md"), encoding="utf-8").read())
assert_clean(rd, "README")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(rd)

# ---- blog post
t = open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: b.fmt(b.get(m.group(1)), m.group(3)), t)
for f in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(BL, f)), f
vis = re.sub(r"<[^>]+>|<!--.*?-->", " ", t)
assert_clean(vis, "blog")
open(os.path.join(BL, "post.html"), "w", encoding="utf-8").write(t)
words = len(re.sub(r"\{\{IMG\|[^}]*\}\}", " ", re.sub(r"<!--.*?-->|<[^>]+>", " ", t)).split())
meta = {"title": "Britain in AD 500: what the ground tells us", "slug": SLUG,
        "excerpt": f"Maps of Britain in AD 500 show neat kingdoms. I mapped what the ground can place instead: {R['n_mapped_not_roman']:,} pieces of evidence, a sharp east of graves and west of stones, and {R['kingdoms']['n']} kingdoms we can name but not draw.",
        "seo_description": f"An evidence-led map of Britain and Ireland around AD 500: hillforts, Anglo-Saxon graves, ogham and Latin stones, and uncertain kingdoms.",
        "tags": ["early medieval", "sub-Roman Britain", "Anglo-Saxons", "hillforts", "ogham", "Picts", "maps", "data"],
        "header_alt": "Title card reading 'Britain in AD 500' in dark ink and madder red on pale vellum, beside a map of Britain and Ireland with purple Pictish, green Irish, teal British and orange Anglo-Saxon hazes, coloured dots for evidence and italic kingdom names."}
assert len(meta["seo_description"]) < 160
assert_clean(json.dumps(meta, ensure_ascii=False), "blog meta")
json.dump(meta, open(os.path.join(BL, "meta.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# ---- Zenodo
shutil.copy(os.path.join(REL, NAME + ".pdf"), os.path.join(ZE, NAME + ".pdf"))
for f in ["evidence.csv", "hillforts_reused.csv", "hillforts_all_counts.csv", "kingdoms.csv", "kingdom_evidence.csv", "civitates.csv", "events.csv",
          "longitude_profile.csv", "timeline_counts.csv", "results.json"]:
    shutil.copy(os.path.join(DATA, f), os.path.join(ZE, f))
zp = os.path.join(ZE, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, fn)
            if os.path.isfile(p) and not fn.endswith(".pyc"):
                z.write(p, f"{SLUG}/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html", "header.png"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(os.path.join(REL, "paper", NAME + ".tex"), encoding="utf-8").read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}\s*(.*?)\n\s*\\textbf\{Keywords", tex, re.S).group(1).strip()
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab).replace("\\%", "%").replace("km\\textsuperscript{2}", "km2").replace("\\&", "&")
assert "\\" not in ab, ab
title = "Britain in AD 500: What the Ground Tells Us. Mapping Early Medieval Evidence and Uncertain Kingdoms in Britain and Ireland from Open Data"
zm = {"title": title,
      "description_html": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: to follow.</p>",
      "keywords": ["sub-Roman Britain", "early medieval archaeology", "hillforts", "Anglo-Saxon cemeteries", "ogham", "inscribed stones", "Pictish stones",
                   "kingdoms", "uncertainty", "open data"],
      "licence": "cc-by-sa-4.0",
      "related": [{"identifier": REPO, "relation": "issupplementedby", "resource_type": "software"},
                  {"identifier": PAGE, "relation": "issupplementedby", "resource_type": "other"},
                  {"identifier": "https://hillforts.arch.ox.ac.uk", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.wikidata.org", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.archaeology.ie", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://pleiades.stoa.org", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://zenodo.org/records/17122148", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://en.wikipedia.org/wiki/Sub-Roman_Britain", "relation": "isderivedfrom", "resource_type": "other"},
                  {"identifier": "https://www.ordnancesurvey.co.uk/products/os-open-names", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.naturalearthdata.com", "relation": "isderivedfrom", "resource_type": "dataset"}]}
assert_clean(json.dumps(zm, ensure_ascii=False), "zenodo meta")
json.dump(zm, open(os.path.join(ZE, "meta.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("blog words", words, "abstract words", len(ab.split()))
