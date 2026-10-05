"""Convierte preannot/*.json -> annot_yolo/{rock}/{base}.txt (YOLO-seg, 48 clases con sufijo).
Sufijo segun manifest (PPL/XPL). Filtra poligonos <3 puntos y clases no mapeadas.
Genera annot_yolo/data.yaml + conversion_report.csv
Uso: python convert_annotations.py [--min-conf 0]
"""
import argparse
import csv
import glob
import json
import os

from PIL import Image

CLASSES = [l.strip() for l in open("classes_ppl_xpl.txt", encoding="utf-8") if l.strip()]
CID = {c: i for i, c in enumerate(CLASSES)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-conf", type=float, default=0.0)
    args = ap.parse_args()

    mani = {}
    for r in csv.DictReader(open("raw_strekeisen/manifest.csv", encoding="utf-8")):
        mani[r["file"]] = r.get("ppl_xpl", "UNKNOWN")
    # mapa json -> file original (via resumen)
    j2f = {}
    if os.path.exists("preannot_resumen.csv"):
        for r in csv.DictReader(open("preannot_resumen.csv", encoding="utf-8")):
            base = os.path.splitext(os.path.basename(r["file"]))[0]
            j2f[(r["rock"], base)] = r["file"]

    files = glob.glob("preannot/*/*.json")
    print(f"JSONs: {len(files)}")
    os.makedirs("annot_yolo", exist_ok=True)
    rep = open("conversion_report.csv", "w", newline="", encoding="utf-8")
    w = csv.DictWriter(rep, fieldnames=["json", "file", "n_pred", "n_poly", "unmapped", "empty"])
    w.writeheader()
    n_poly = n_empty = n_unmap = 0
    for jp in files:
        rock = os.path.basename(os.path.dirname(jp))
        base = os.path.splitext(os.path.basename(jp))[0]
        f = j2f.get((rock, base))
        if not f or not os.path.exists(f):
            # fallback: reconstruir ruta desde manifest por nombre base
            cands = [k for k in mani if os.path.splitext(os.path.basename(k))[0] == base]
            f = cands[0] if cands else ""
        if not f or not os.path.exists(f):
            w.writerow({"json": jp, "file": f, "n_pred": 0, "n_poly": 0,
                        "unmapped": "", "empty": "no-file"})
            continue
        ill = mani.get(f, "UNKNOWN")
        d = json.load(open(jp, encoding="utf-8"))
        W, H = Image.open(f).size
        lines, unmapped = [], set()
        for p in d.get("predictions", []):
            if float(p.get("confidence", 0)) < args.min_conf:
                continue
            pts = p.get("points", [])
            if len(pts) < 3:
                continue
            cls = f"{p.get('class', '?')}_{ill}"
            if cls not in CID:
                unmapped.add(str(p.get("class")))
                continue
            xy = " ".join(f"{min(max(pt['x'] / W, 0), 1):.6f} {min(max(pt['y'] / H, 0), 1):.6f}"
                          for pt in pts)
            lines.append(f"{CID[cls]} {xy}")
        out_dir = os.path.join("annot_yolo", rock)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, base + ".txt"), "w", encoding="utf-8") as fo:
            fo.write("\n".join(lines) + ("\n" if lines else ""))
        n_poly += len(lines)
        if not lines:
            n_empty += 1
        n_unmap += len(unmapped)
        w.writerow({"json": jp, "file": f, "n_pred": len(d.get("predictions", [])),
                    "n_poly": len(lines), "unmapped": ";".join(sorted(unmapped)),
                    "empty": (not lines)})
    rep.close()
    with open("annot_yolo/data.yaml", "w", encoding="utf-8") as fy:
        fy.write("train: ../raw_strekeisen\nval: ../raw_strekeisen\n\nnc: 48\nnames:\n")
        for i, c in enumerate(CLASSES):
            fy.write(f"  {i}: {c}\n")
    print(f"Poligonos: {n_poly} | vacios: {n_empty} | unmapped: {n_unmap}")


if __name__ == "__main__":
    main()