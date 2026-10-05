"""Seleccion subset v1: maficos pluto/vulc + top prioridad con candidatas. -> dataset_v1.csv"""
import csv

MAFICAS = {"gabbro", "eufodite", "gabbroaugite", "gabbronorite", "olivinegabbro",
           "gabbrohornblende", "mattonigabbro", "mattoni", "norite", "troctolite",
           "dun", "dunite", "basalt", "ankaramite", "wherlite", "harzburgite",
           "finero", "peridotites", "pyroxenite", "orthopyroxenite", "olivine",
           "clinopyroxene", "cumberlandite", "hornblendite", "hornblendite1",
           "ijolite", "ijolite1", "melteigite", "jacupirangite", "kentallenite",
           "diorite", "monzodiorite", "rhum", "orthocumulates", "adcumulates",
           "quartzgabbro", "lherzoliteserpentinized",
           "garnetlherzolite", "spinelehorzolite"}

import os

rows = [r for r in csv.DictReader(open("raw_strekeisen/manifest.csv", encoding="utf-8"))
        if r.get("ppl_xpl") in ("PPL", "XPL") and os.path.exists(r["file"])]
mafic = [r for r in rows if r["family"] in ("pluto", "vulc") and r["rock"] in MAFICAS]
picked = {r["file"] for r in mafic}
rest = [r for r in rows if r["file"] not in picked]

# importar candidatas de weak_labels sin reejecutar: recalculo rapido inline
import re
PATS = [("clinopyroxene", "Clinopiroxeno"), ("orthopyroxene", "Ortopiroxeno"),
        ("aegirine", "Aegirina"), ("olivine", "Olivino"), ("plagioclase", "Plagioclasa"),
        ("quartz", "Cuarzo"), ("hornblende", "Hornblenda"), ("amphibole", "Anfibol"),
        ("biotite", "Flogopita"), ("nepheline", "nefelina"), ("sodalite", "Sodalita"),
        ("cancrinite", "Cancrinita"), ("calcite", "Calcita"), ("orthoclase", "Ortoclasa"),
        ("sanidine", "Ortoclasa"), ("antiperthite", "Antipertita"), ("perthite", "Antipertita"),
        ("arfvedsonite", "Arfvedsonita"), ("eudialyte", "Eudialita"), ("eudialite", "Eudialita"),
        ("rosenbuschite", "Rusenbuschita"), ("ilmenite", "Ilmenita"), ("magnetite", "Mineral opaco"),
        ("opaque", "Mineral opaco"), ("tourmaline", "Turmalina"), ("serpentine", "Venas de serpentina"),
        ("augite", "Clinopiroxeno"), ("pyroxene", "Piroxeno")]


def ncands(cap):
    cap = (cap or "").lower()
    return sum(1 for en, _ in PATS if re.search(r"\b" + en + r"s?\b", cap))


scored = []
for r in rest:
    n = ncands(r.get("caption", ""))
    bonus = 1 if r["family"] in ("pluto", "vulc") else 0
    scored.append((n * 2 + bonus, r))
scored.sort(key=lambda t: -t[0])
extra = [r for s, r in scored if s >= 2][:500]

v1 = ([{**r, "source": "mafico"} for r in mafic] +
      [{**r, "source": "priority"} for r in extra])
with open("dataset_v1.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file", "family", "rock", "ppl_xpl", "mag",
                                      "caption", "source"])
    w.writeheader()
    for r in v1:
        w.writerow({k: r.get(k, "") for k in
                    ["file", "family", "rock", "ppl_xpl", "mag", "caption", "source"]})
from collections import Counter
print(f"v1: {len(v1)} (maficos {len(mafic)}, priority {len(extra)})")
print(Counter(r["ppl_xpl"] for r in v1))
print(Counter(r["family"] for r in v1).most_common())
