from roboflow import Roboflow
import config

rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
ws = rf.workspace(config.ROBOFLOW_WORKSPACE)
print(f"Workspace: {config.ROBOFLOW_WORKSPACE} OK")

project = ws.project(config.ROBOFLOW_PROJECT)
print(f"Proyecto: {project.name} | tipo: {project.type}")

version = project.version(config.ROBOFLOW_VERSION)
print(f"Version {config.ROBOFLOW_VERSION} cargada OK")

model = version.model
print(f"Modelo: {model}")
print("Conexion exitosa. Listo para predecir.")
