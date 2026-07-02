from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware



from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import MODE
from services.gate_service import GateService
from security.auth import require_api_key

app = FastAPI(title="Gate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gate_service = GateService()


@app.get("/api")
def root():
    return {
        "message": "Backend beží",
        "mode": MODE,
    }


@app.get("/api/health")
def health():
    snapshot = gate_service.get_status()
    return {
        "backend": "ok",
        "device_mode": MODE,
        "device_status": "offline" if snapshot["state"] == "offline" else "ok",
        "gate": snapshot,
    }


@app.get("/api/status")
def status():
    return gate_service.get_status()


@app.post("/api/open", dependencies=[Depends(require_api_key)])
def open_gate():
    return gate_service.open_gate()


@app.post("/api/close", dependencies=[Depends(require_api_key)])
def close_gate():
    return gate_service.close_gate()


@app.get("/api/gates")
def get_all_gates():
    return gate_service.get_all_gates_status()


@app.get("/api/gates/{gate_id}/status")
def get_gate_status(gate_id: int):
    return gate_service.get_gate_status(gate_id)


@app.post("/api/gates/{gate_id}/open", dependencies=[Depends(require_api_key)])
def open_gate_by_id(gate_id: int):
    return gate_service.open_gate_by_id(gate_id)


@app.post("/api/gates/{gate_id}/close", dependencies=[Depends(require_api_key)])
def close_gate_by_id(gate_id: int):
    return gate_service.close_gate_by_id(gate_id)


@app.post("/api/reset", dependencies=[Depends(require_api_key)])
def reset_gate():
    return gate_service.reset_gate()


@app.post("/api/fault", dependencies=[Depends(require_api_key)])
def fault_gate():
    return gate_service.fault_gate()


@app.post("/api/offline", dependencies=[Depends(require_api_key)])
def offline_gate():
    return gate_service.offline_gate()


frontend_build_path = os.path.join(os.path.dirname(__file__), "frontend", "build")

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(frontend_build_path, "static")),
    name="static",
)

@app.get("/{full_path:path}")
def serve_react(full_path: str):
    index_file = os.path.join(frontend_build_path, "index.html")
    return FileResponse(index_file)
