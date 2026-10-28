"""Step 4. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift from
the analysis. The evidence points, kingdoms and chart data (work/site_data.json, from step 3) are embedded; the map
images, coast, roads and place list are small files in data/.
Run: python3 code/04_build_site.py
"""
import json, os, re
from common import *

R = json.load(open(os.path.join(DATA, "results.json"), encoding="utf-8"))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f in ("f1", "x1"): return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "w2":
        assert v < 0
        return f"{-v:.2f}"
    raise ValueError(f)


TOK = r"\{\{([^}|]+)(\|(\w+))?\}\}"
# statements the template makes in words, checked against the data
assert R["eastwest"]["germanic_median_lon"] > -1 and R["eastwest"]["brittonic_median_lon"] < -3
assert R["surfaces"]["ger_brit_overlap_km2"] == 0 and R["eastwest"]["brit_within_50km_of_ger"] == 1
assert R["hill"]["coastal_share"] > R["hill"]["coastal_all_share"] and R["hill"]["promontory_share"] > R["hill"]["promontory_all_share"]
assert R["hill"]["by_country"]["Isle of Man"]["share"] == max(v["share"] for v in R["hill"]["by_country"].values())
z = {k["name"]: k for k in R["kingdoms"]["zones"]}
assert z["Gododdin"]["pictish"] > 0 and z["Gododdin"]["brittonic"] == 0
assert z["Elmet"]["brittonic"] + z["Elmet"]["germanic"] == 0 and z["Ergyng"]["n"] == 0
for k in ("Kent", "Sussex", "East Angles", "Gewisse (later Wessex)"):
    assert z[k]["matching_share"] >= 0.9
for k in ("Gwynedd", "Dyfed", "Glywysing", "Brycheiniog"):
    assert z[k]["matching_share"] >= 0.9
assert R["roman"]["ger_town_med_km"] < R["roman"]["random_town_med_km"]
assert R["kingdoms"]["groups"] == {"brittonic": 14, "irish": 1, "pictish": 1, "germanic": 8}
for art, ph in [("Wroxeter", "early post-Roman capital of Powys"), ("Kingdom of Dyfed", "late Imperial Roman title of \"protector\""),
                ("De Excidio et Conquestu Britanniae", "the difference in spelling has led some to suggest that they are not the same person"),
                ("Ogham", "used primarily to write the early Irish language"), ("Ogham", "flourished in the 5th and 6th centuries around the Irish Sea"),
                ("Y Gododdin", "later 13th century"), ("Historia Brittonum", "9th"), ("Deira", "completed in 731"),
                ("Anglo-Saxon Chronicle", "9th"), ("Dunadd", "coronation ritual"), ("Brycheiniog", "late fifth century"),
                ("Volcanic winter of 536", "cooling the atmosphere for several years"), ("Plague of Justinian", "Edix Hill")]:
    check_quote(art, ph)

if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    SITE = open(os.path.join(WORK, "site_data.json"), encoding="utf-8").read()
    html = re.sub(TOK, lambda m: fmt(get(m.group(1)), m.group(3)), tpl)
    slim = {"hill": {"by_country": R["hill"]["by_country"]}}
    html = html.replace("/*SITE*/", SITE).replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S))
    assert_clean(vis, "page text")
    # strings inside the script that become visible text
    scr = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    for s_ in re.findall(r'"([^"\n]{12,})"|`([^`]{12,})`', scr):
        for t in s_:
            if t: assert "\u2014" not in t and "\u2013" not in t, t[:80]
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html) // 1024, "KB")
