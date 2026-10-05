"""Filtro v1: consistencia caption + YOLO-seg 24 clases (sin sufijo).
Regla: caption con candidatas -> solo poligonos de esas clases;
       caption sin candidatas -> solo conf>=30. Min 3 puntos.
Salida: annot_v1/{rock}/{base}.txt + filter_report.csv + manual_queue.csv
Uso: python filter_v1.py
"""
import csv
import glob
import json
import os
from collections import Counter

from PIL import Image

from weak_labels import candidates as cap_candidates

CLASSES = [l.strip() for l in open("classes24.txt", encoding="utf-8") if l.strip()]
CID = {c: i for i, c in enumerate(CLASSES)}
CAP2BASE = {}  # caption (lower) -> file meta
for r in csv.DictReader(open("dataset_v1.csv", encoding="utf-8")):
    CAP2BASE[r["file"]] = r


def main():
    j2f = {}
    if os.path.exists("preannot_resumen.csv"):
        for r in csv.DictReader(open("preannot_resumen.csv", encoding="utf-8")):
            base = os.path.splitext(os.path.basename(r["file"]))[0]
            j2f[(r["rock"], base)] = r["file"]

    files = glob.glob("preannot/*/*.json")
    kept_cls = Counter()
    rep = open("filter_report.csv", "w", newline="", encoding="utf-8")
    w = csv.DictWriter(rep, fieldnames=["file", "rock", "ppl_xpl", "n_raw", "n_kept",
                                        "candidatas", "motivo"])
    w.writeheader()
    manual = []
    n_kept = n_raw = 0
    for jp in files:
        rock = os.path.basename(os.path.dirname(jp))
        base = os.path.splitext(os.path.basename(jp))[0]
        f = j2f.get((rock, base))
        if not f or f not in CAP2BASE or not os.path.exists(f):
            continue
        meta = CAP2BASE[f]
        cands, _ = cap_candidates(meta.get("caption", ""))
        d = json.load(open(jp, encoding="utf-8"))
        preds = d.get("predictions", [])
        n_raw += len(preds)
        W, H = Image.open(f).size
        lines = []
        for p in preds:
            conf = float(p.get("confidence", 0))
            cls = str(p.get("class", "?"))
            pts = p.get("points", [])
            if len(pts) < 3 or cls not in CID:
                continue
            if cands:
                # caption es ilustrativa, no exhaustiva: respeta candidatas
                # pero rescata detecciones de alta confianza aunque no se nombren
                if cls not in cands and conf < 0.40:
                    continue
            elif conf < 0.30:
                continue
            xy = " ".join(f"{min(max(pt['x'] / W, 0), 1):.6f} {min(max(pt['y'] / H, 0), 1):.6f}"
                          for pt in pts)
            lines.append(f"{CID[cls]} {xy}")
            kept_cls[cls] += 1
        out_dir = os.path.join("annot_v1", rock)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, base + ".txt"), "w", encoding="utf-8") as fo:
            fo.write("\n".join(lines) + ("\n" if lines else ""))
        n_kept += len(lines)
        motivo = "ok" if lines else ("vacia-ocr" if not preds else "filtro-caption")
        if not lines:
            manual.append({"file": f, "rock": rock, "ppl_xpl": meta["ppl_xpl"],
                           "n_raw": len(preds), "motivo": motivo,
                           "caption": meta.get("caption", "")})
        w.writerow({"file": f, "rock": rock, "ppl_xpl": meta["ppl_xpl"],
                    "n_raw": len(preds), "n_kept": len(lines),
                    "candidatas": ";".join(cands), "motivo": motivo})
    rep.close()
    with open("manual_queue.csv", "w", newline="", encoding="utf-8") as f:
        ww = csv.DictWriter(f, fieldnames=["file", "rock", "ppl_xpl", "n_raw",
                                           "motivo", "caption"])
        ww.writeheader()
        ww.writerows(manual)
    with open("annot_v1/data.yaml", "w", encoding="utf-8") as fy:
        fy.write("train: ../dataset_v1_images\nval: ../dataset_v1_images\n\nnc: 24\nnames:\n")
        for i, c in enumerate(CLASSES):
            fy.write(f"  {i}: {c}\n")
    print(f"JSONs v1 procesados | raw: {n_raw} kept: {n_kept} | manual: {len(manual)}")
    print("Top kept:", kept_cls.most_common(8))


if __name__ == "__main__":
    main()
