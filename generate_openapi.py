import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from strict_models import BusquedaRequest, BusquedaResponse, TaskResponse, ProgressResponse

app = FastAPI()

@app.post("/buscar-fechas-v2", response_model=BusquedaResponse)
async def buscar_fechas_v2(request: BusquedaRequest):
    pass

@app.post("/buscar", response_model=TaskResponse)
async def buscar(request: BusquedaRequest):
    pass

@app.get("/progress/{task_id}", response_model=ProgressResponse)
async def progress(task_id: str):
    pass

def generate_openapi_spec():
    openapi_schema = get_openapi(
        title="Carta Electiva API Strict",
        version="1.0.0",
        description="Strict API for Electional Chart",
        routes=app.routes,
    )
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("OpenAPI spec generated at openapi.json")

if __name__ == "__main__":
    generate_openapi_spec()
