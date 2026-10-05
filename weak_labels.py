"""Etiquetas debiles: captions EN -> clases ES candidatas + sufijo PPL/XPL.
Genera annotation_queue.csv y queue_priority.csv
Uso: python weak_labels.py
"""
import csv
import os
import re
from collections import Counter

# patron EN (minusculas) -> clase ES base
EN2ES = [
    ("clinopyroxene", "Clinopiroxeno"), ("orthopyroxene", "Ortopiroxeno"),
    ("augite", "Clinopiroxeno"), ("enstatite", "Ortopiroxeno"),
    ("hypersthene", "Ortopiroxeno"), ("olivine", "Olivino"),
    ("plagioclase", "Plagioclasa"), ("quartz", "Cuarzo"),
    ("hornblende", "Hornblenda"), ("amphibole", "Anfibol"),
    ("biotite", "Flogopita"), ("phlogopite", "Flogopita"),
    ("aegirine", "Aegirina"), ("nepheline", "nefelina"),
    ("sodalite", "Sodalita"), ("cancrinite", "Cancrinita"),
    ("calcite", "Calcita"), ("sanidine", "Ortoclasa"),
    ("alkali feldspar", "Ortoclasa"), ("orthoclase", "Ortoclasa"),
    ("antiperthite", "Antipertita"), ("perthite", "Antipertita"),
    ("arfvedsonite", "Arfvedsonita"), ("eudialyte", "Eudialita"),
    ("eudialite", "Eudialita"), ("rosenbuschite", "Rusenbuschita"),
    ("ilmenite", "Ilmenita"), ("magnetite", "Mineral opaco"),
    ("opaque", "Mineral opaco"), ("tourmaline", "Turmalina"),
    ("serpentine", "Venas de serpentina"), ("mesh texture", "Olivino alterado con serpentina"),
    ("iddingsite", "Olivino alterado con serpentina"),
    ("bowlingite", "Olivino alterado con serpentina"),
    ("pyroxene", "Piroxeno"), ("kaersutite", "Hornblenda"),
    ("uralite", "Hornblenda"),
]
# minerales mencionados sin clase en taxonomia -> aviso
SIN_CLASE = ["apatite", "garnet", "zircon", "titanite", "chromite",
             "leucite", "melilite", "spinel", "carbonate", "feldspar"]


def candidates(caption):
    cap = (caption or "").lower()
    out = []
    for en, es in EN2ES:
        if re.search(r"\b" + re.escape(en) + r"s?\b", cap):
            if es not in out:
                out.append(es)
    flags = [w for w in SIN_CLASE if re.search(r"\b" + w + r"s?\b", cap)]
    return out, flags


def main():
    rows = list(csv.DictReader(open("raw_strekeisen/manifest.csv", encoding="utf-8")))
    q = []
    for r in rows:
        cands, flags = candidates(r.get("caption", ""))
        ill = r.get("ppl_xpl", "UNKNOWN")
        if ill in ("PPL", "XPL"):
            suff = [f"{c}_{ill}" for c in cands]
        else:
            suff = [f"{c}_PPL/{c}_XPL?" for c in cands]
        # prioridad: iluminacion conocida + >=1 candidato + familia ignea
        score = (1 if ill in ("PPL", "XPL") else 0) + (2 if cands else 0) \
            + (1 if r.get("family") in ("pluto", "vulc") else 0)
        q.append({"file": r["file"], "family": r["family"], "rock": r["rock"],
                  "ppl_xpl": ill, "mag": r.get("mag", ""),
                  "candidatas": ";".join(suff), "sin_clase": ";".join(flags),
                  "caption": r.get("caption", ""), "score": score})
    q.sort(key=lambda d: -d["score"])
    with open("annotation_queue.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "family", "rock", "ppl_xpl", "mag",
                                          "candidatas", "sin_clase", "caption", "score"])
        w.writeheader()
        w.writerows(q)
    prio = [d for d in q if d["score"] >= 3]
    with open("queue_priority.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "family", "rock", "ppl_xpl", "mag",
                                          "candidatas", "sin_clase", "caption", "score"])
        w.writeheader()
        w.writerows(prio)
    unk = sum(1 for d in q if d["ppl_xpl"] == "UNKNOWN")
    noc = sum(1 for d in q if not d["candidatas"])
    print(f"Cola total: {len(q)} | prioridad>=3: {len(prio)} | UNKNOWN: {unk} | sin candidatas: {noc}")
    print("Top clases candidatas:")
    c = Counter()
    for d in q:
        for s in d["candidatas"].split(";"):
            if s:
                c[s.split("_PPL")[0].split("_XPL")[0]] += 1
    for k, v in c.most_common(12):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
