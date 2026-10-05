"""PetroTerratech API: yolov8n-seg instance segmentation de minerales en seccion delgada.
Corre en Hugging Face Spaces (CPU). Expone /predict para la web estatica Firebase.
"""
import io
import json

import gradio as gr
from PIL import Image
from ultralytics import YOLO

MODEL = YOLO("weights.pt")
NAMES = MODEL.names  # {id: mineral}


def predict(img: Image.Image, conf: float):
    if img is None:
        return None, "[]"
    if img.mode != "RGB":
        img = img.convert("RGB")
    r = MODEL.predict(img, conf=float(conf), imgsz=640, verbose=False)[0]
    dets = []
    if r.masks is not None and r.boxes is not None:
        W, H = img.size
        for i, box in enumerate(r.boxes):
            cls = int(box.cls[0])
            poly = (r.masks.xy[i] if hasattr(r.masks, "xy") else []).tolist()
            dets.append({"class": NAMES.get(cls, str(cls)),
                         "confidence": round(float(box.conf[0]), 3),
                         "polygon": [[round(float(x), 1), round(float(y), 1)] for x, y in poly],
                         "img_w": W, "img_h": H})
    annotated = Image.fromarray(r.plot()[..., ::-1])
    return annotated, json.dumps(dets, ensure_ascii=False)


demo = gr.Interface(
    fn=predict,
    inputs=[gr.Image(type="pil", label="Seccion delgada"),
            gr.Slider(0.05, 0.9, value=0.25, step=0.05, label="Confianza")],
    outputs=[gr.Image(label="Minerales detectados"),
             gr.Textbox(label="Detecciones JSON")],
    title="PetroTerratech - Identificacion de minerales en seccion delgada (demo v1)",
    description="YOLOv8n-seg 24 clases. Modelo v1 en entrenamiento activo: resultados parciales.",
    api_name="predict",
)
demo.launch()
