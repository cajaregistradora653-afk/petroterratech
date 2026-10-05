"""Identificacion de minerales en seccion delgada (instance-segmentation)."""
import argparse
import json
import os
from collections import Counter

import cv2
import numpy as np
from roboflow import Roboflow

import config


def get_model(project_name="", version=0):
    project_name = project_name or config.ROBOFLOW_PROJECT
    version = version or config.ROBOFLOW_VERSION
    rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
    project = rf.workspace(config.ROBOFLOW_WORKSPACE).project(project_name)
    return project.version(version).model, project_name, version


def draw_predictions(image_path: str, predictions: dict, out_path: str):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"No se pudo leer imagen: {image_path}")
    overlay = img.copy()

    for pred in predictions.get("predictions", []):
        pts = pred.get("points", [])
        cls = pred.get("class", "?")
        conf = pred.get("confidence", 0)
        if len(pts) >= 3:
            poly = np.array([[int(p["x"]), int(p["y"])] for p in pts], dtype=np.int32)
            color = tuple(int(c) for c in np.random.default_rng(abs(hash(cls)) % 2**32).integers(0, 255, 3))
            cv2.fillPoly(overlay, [poly], color)
            cv2.polylines(img, [poly], True, color, 2)
            x, y = int(poly[0][0]), max(0, int(poly[0][1]) - 8)
            cv2.putText(img, f"{cls} {conf:.2f}", (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    blended = cv2.addWeighted(overlay, 0.4, img, 0.6, 0)
    # re-dibujar contornos sobre mezcla para nitidez
    for pred in predictions.get("predictions", []):
        pts = pred.get("points", [])
        if len(pts) >= 3:
            poly = np.array([[int(p["x"]), int(p["y"])] for p in pts], dtype=np.int32)
            cv2.polylines(blended, [poly], True, (255, 255, 255), 1)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cv2.imwrite(out_path, blended)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imagen", help="Ruta a foto de seccion delgada")
    ap.add_argument("--confidence", type=int, default=40, help="Umbral 0-100 (default 40)")
    ap.add_argument("--project", default="", help="Override proyecto (ej. petroterratech)")
    ap.add_argument("--version", type=int, default=0, help="Override version")
    ap.add_argument("--out", default="", help="Ruta salida anotada")
    ap.add_argument("--json-out", default="", help="Guardar JSON crudo")
    args = ap.parse_args()

    model, proj, ver = get_model(args.project, args.version)
    print(f"Prediciendo {args.imagen} con {proj}/v{ver} ...")
    result = model.predict(args.imagen, confidence=args.confidence).json()

    preds = result.get("predictions", [])
    conteo = Counter(p.get("class", "?") for p in preds)
    print(f"Detecciones: {len(preds)}")
    for mineral, n in conteo.most_common():
        print(f"  - {mineral}: {n}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"JSON guardado en {args.json_out}")

    out = args.out or os.path.join("outputs", "pred_" + os.path.basename(args.imagen))
    draw_predictions(args.imagen, result, out)
    print(f"Imagen anotada en {out}")


if __name__ == "__main__":
    main()
