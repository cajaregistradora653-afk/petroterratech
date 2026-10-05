"""Entrena petroterratech v1 en Roboflow (fast). Uso: python train_v1.py"""
from roboflow import Roboflow
import config

rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
project = rf.workspace(config.ROBOFLOW_WORKSPACE).project("petroterratech")
version = project.version(1)
print("Entrenando v1 (fast)...")
version.train(speed="fast", model_type="yolov8n-seg")
print("Entrenamiento lanzado. Monitorea en Roboflow UI -> petroterratech -> Versions -> 1 -> Train.")
