import os
from dotenv import load_dotenv

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_WORKSPACE = os.getenv("ROBOFLOW_WORKSPACE", "proyect-terratech")
ROBOFLOW_PROJECT = os.getenv("ROBOFLOW_PROJECT", "identificacion-de-minerales")
ROBOFLOW_VERSION = int(os.getenv("ROBOFLOW_VERSION", "2"))

if not ROBOFLOW_API_KEY:
    raise RuntimeError("Falta ROBOFLOW_API_KEY en .env")
