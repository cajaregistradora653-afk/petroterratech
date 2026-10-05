"""Render QA: dibuja annot_v1 sobre 2 imagenes ok -> outputs/qa_v1_a/b.jpg"""
import csv
import os

import cv2
import numpy as np

CLASSES = [l.strip() for l in open("classes24.txt", encoding="utf-8") if l.strip()]

rows = [r for r in csv.DictReader(open("filter_report.csv", encoding="utf-8"))
        if r["motivo"] == "ok"]
print(f"ok disponibles: {len(rows)}")
for tag, r in zip(("a", "b"), [rows[0], rows[len(rows) // 2]]):
    img = cv2.imread(r["file"])
    H, W = img.shape[:2]
    ov = img.copy()
    base = os.path.splitext(os.path.basename(r["file"]))[0]
    n = 0
    for ln in open(f"annot_v1/{r['rock']}/{base}.txt", encoding="utf-8"):
        p = ln.split()
        cid = int(p[0])
        xy = np.array(p[1:], float).reshape(-1, 2)
        xy[:, 0] *= W
        xy[:, 1] *= H
        poly = xy.astype(np.int32)
        col = tuple(int(c) for c in np.random.default_rng(cid).integers(0, 255, 3))
        cv2.fillPoly(ov, [poly], col)
        cv2.polylines(img, [poly], True, col, 2)
        cv2.putText(img, CLASSES[cid], tuple(poly[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2)
        n += 1
    out = f"outputs/qa_v1_{tag}.jpg"
    cv2.imwrite(out, cv2.addWeighted(ov, 0.4, img, 0.6, 0))
    print(tag, r["file"], "poligonos:", n, "->", out)
