from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.core.config import settings
from backend.core.exceptions import ModelNotLoadedError, InvalidPcapError
from backend.api import system, detect, alerts, model, ws

app = FastAPI(title="NIDS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(detect.router)
app.include_router(alerts.router)
app.include_router(model.router)
app.include_router(ws.router)


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"success": False, "data": None, "error": str(exc)},
    )


@app.exception_handler(InvalidPcapError)
async def invalid_pcap_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"success": False, "data": None, "error": str(exc)},
    )


@app.get("/")
async def root():
    return {"success": True, "data": {"service": "NIDS API", "version": "1.0.0"}}
