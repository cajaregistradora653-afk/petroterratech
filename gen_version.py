"""Genera version 1 de petroterratech: remap numerico->nombres + preprocess + augment.
Uso: python gen_version.py
"""
import json

from roboflow import Roboflow
import config

NAMES = [l.strip() for l in open("classes24.txt", encoding="utf-8") if l.strip()]

rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
project = rf.workspace(config.ROBOFLOW_WORKSPACE).project("petroterratech")

# '4' (Calcita) y '15' (Clinopiroxeno) no existen en el proyecto (0 poligonos)
MISSING = {"4", "15"}
settings = {
    "preprocessing": {
        "auto-orient": True,
        "resize": {"width": 640, "height": 640, "format": "Stretch to"},
        "remap": {str(i): n for i, n in enumerate(NAMES) if str(i) not in MISSING},
        "filter-null": {"percent": 100},
    },
    "augmentation": {
        "flip": {"horizontal": True, "vertical": False},
        "rotate": {"degrees": 15},
        "image": {"versions": 3},
    },
}
v = project.generate_version(settings=settings)
print(f"Generando version: {v}")
with open("version_v1.txt", "w", encoding="utf-8") as f:
    f.write(str(v))
