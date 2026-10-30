"""
AI Side-Channel Attack Detector - Cyberpunk Web Dashboard
FastAPI + WebSockets + HTML5 Canvas 60 FPS Oscilloscope.
"""

import os
import sys
import asyncio
import json
import webbrowser
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from core.detector_engine import DetectorEngine, SystemState


app = FastAPI(title="AI-SCA Side-Channel Attack Detector & Defense")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")

# Core Engine instance
engine = DetectorEngine()

# Active WebSocket connections
active_connections: list[WebSocket] = []
main_loop: asyncio.AbstractEventLoop = None


class ConnectPayload(BaseModel):
    port: str = "COM7"
    baud: int = 115200
    simulation: bool = False


class ThresholdPayload(BaseModel):
    threshold: float = 10.0


class AutoDefensePayload(BaseModel):
    enabled: bool = True


# -----------------------------------------------------------------------------
# ENGINE EVENT ADAPTER
# -----------------------------------------------------------------------------
def on_engine_event(event_type: str, data: Dict[str, Any]):
    """Broadcast log entries to connected web clients."""
    if event_type == "log" and main_loop is not None and main_loop.is_running():
        message_json = json.dumps({"type": "log", "data": data})
        for ws in list(active_connections):
            try:
                asyncio.run_coroutine_threadsafe(ws.send_text(message_json), main_loop)
            except Exception:
                pass

engine.add_listener(on_engine_event)


# -----------------------------------------------------------------------------
# HTTP ROUTES
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/ports")
async def get_ports():
    ports = DetectorEngine.get_available_ports()
    return {"ports": ports}


@app.post("/api/connect")
async def api_connect(payload: ConnectPayload):
    engine.start(port=payload.port, baud_rate=payload.baud, simulation=payload.simulation)
    return {"status": "started", "state": engine.state}


@app.post("/api/disconnect")
async def api_disconnect():
    engine.stop()
    return {"status": "stopped", "state": engine.state}


@app.post("/api/retrain")
async def api_retrain():
    engine.retrain()
    return {"status": "retraining"}


@app.post("/api/trigger_button")
async def api_trigger_button():
    """Toggle physical disturbance button."""
    is_active = engine.trigger_physical_change()
    return {"status": "triggered", "active": is_active, "state": engine.state}


@app.post("/api/reset_safe")
async def api_reset_safe():
    """Instantly force the system into SAFE / SECURE mode."""
    engine.reset_to_safe()
    return {"status": "safe", "active": False, "state": engine.state}


@app.post("/api/toggle_defense")
async def api_toggle_defense():
    """Toggle dynamic power masking countermeasure."""
    is_active = engine.toggle_defense()
    return {"status": "toggled", "active": is_active}


@app.post("/api/auto_defense")
async def api_auto_defense(payload: AutoDefensePayload):
    engine.set_auto_defense(payload.enabled)
    return {"status": "updated", "enabled": payload.enabled}


@app.post("/api/threshold")
async def api_threshold(payload: ThresholdPayload):
    engine.set_min_change(payload.threshold)
    return {"status": "updated", "threshold": payload.threshold}


@app.get("/api/snapshot")
async def api_snapshot():
    return engine.get_snapshot()


# -----------------------------------------------------------------------------
# WEBSOCKET STREAM ROUTE (~22 Hz TELEMETRY BROADCAST - SMOOTH & NO STRACKING)
# -----------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            snapshot = engine.get_snapshot()
            await websocket.send_text(json.dumps({"type": "snapshot", "data": snapshot}))
            await asyncio.sleep(0.045)  # ~22 FPS - Smooth, low latency, zero UI freezing
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)


# -----------------------------------------------------------------------------
# SERVER RUNNER
# -----------------------------------------------------------------------------
def run_web(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    global main_loop
    import threading

    print("=" * 65)
    print("  AI SIDE-CHANNEL DETECTOR & POWER MASKING // CYBERPUNK WEB UI")
    print("=" * 65)
    print(f"Server URL: http://{host}:{port}")
    print("Dynamic Power Masking • Real-time INA219 Oscilloscope • SSD1306 Mirror")
    print("=" * 65)

    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)
    main_loop.run_until_complete(server.serve())


if __name__ == "__main__":
    run_web()
