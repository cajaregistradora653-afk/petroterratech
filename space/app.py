"""PetroTerratech API: yolov8n-seg instance segmentation de minerales en seccion delgada.
Corre en Hugging Face Spaces (CPU). Expone /predict para la web estatica Firebase.
"""
import io
import json

import gradio as gr
import spaces
from PIL import Image
from ultralytics import YOLO

MODEL = YOLO("weights.pt")
NAMES = MODEL.names  # {id: mineral}


@spaces.GPU(duration=15)
def predict(img: Image.Image, conf: float):
    try:
        return _predict(img, conf)
    except Exception as e:
        import traceback
        err = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=8)}"
        blank = img.convert("RGB") if img is not None else Image.new("RGB", (64, 64))
        return blank, json.dumps([{"class": "ERROR", "confidence": 0.0,
                                   "polygon": [], "detail": err}])


def _predict(img: Image.Image, conf: float):
    if img is None:
        return None, "[]"
    if img.mode != "RGB":
        img = img.convert("RGB")
    r = MODEL.predict(img, conf=float(conf), imgsz=512, verbose=False)[0]
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
    description="YOLOv8s-seg 23 clases. Modelo v2 en mejora activa: solo rocas plutonicas.",
    api_name="predict",
)
demo.launch(show_error=True)
