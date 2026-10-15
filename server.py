"""Web arayüzü: python server.py  ->  http://127.0.0.1:8000

Yalnızca yerel makinede (127.0.0.1) dinler. /start, kullanıcıdan gelen bir
tarayıcı yolunu çalıştırdığı için başka sitelerden gelen istekler (Origin
kontrolü) reddedilir ve CORS açılmaz.
"""
import argparse
import asyncio
import socket
import threading
import uuid
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse

from cleaner import Config, run

INDEX = Path(__file__).parent / "frontend" / "index.html"
app = FastAPI(title="XCleaner", docs_url=None, redoc_url=None)


@dataclass
class Job:
    cfg: Config
    stop: threading.Event = field(default_factory=threading.Event)
    status: str = "pending"      # pending | running | done
    total: int = 0


jobs: dict[str, Job] = {}


def origin_ok(origin: Optional[str]) -> bool:
    """Origin yoksa (curl vb.) veya yerel adresse izin ver."""
    if not origin:
        return True
    return urlparse(origin).hostname in {"127.0.0.1", "localhost"}


@app.get("/")
async def root():
    return FileResponse(INDEX)


@app.post("/start")
async def start(
    request: Request,
    username: str = Form(...),
    browser_path: str = Form(""),
    profile_dir: str = Form(""),
    attach: str = Form(""),
    dry_run: bool = Form(False),
    max_delete: int = Form(0),
):
    if not origin_ok(request.headers.get("origin")):
        raise HTTPException(403, "İzin verilmeyen kaynak.")
    if any(j.status == "running" for j in jobs.values()):
        raise HTTPException(409, "Zaten çalışan bir işlem var.")

    cfg = Config(
        username=username, browser_path=browser_path, profile_dir=profile_dir or "browser_profile",
        attach=attach.strip(), dry_run=dry_run, max_delete=max_delete,
    )
    try:
        cfg.validate()
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    jobs.clear()
    job_id = uuid.uuid4().hex[:8]
    jobs[job_id] = Job(cfg=cfg)
    return {"job_id": job_id}


@app.post("/stop/{job_id}")
async def stop(job_id: str, request: Request):
    if not origin_ok(request.headers.get("origin")):
        raise HTTPException(403, "İzin verilmeyen kaynak.")
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "İşlem bulunamadı.")
    job.stop.set()
    return {"ok": True}


@app.websocket("/ws/{job_id}")
async def ws(websocket: WebSocket, job_id: str):
    if not origin_ok(websocket.headers.get("origin")):
        await websocket.close(code=1008)
        return
    await websocket.accept()

    job = jobs.get(job_id)
    if job is None or job.status != "pending":
        await websocket.send_json({"type": "log", "msg": "İşlem bulunamadı ya da zaten başlatılmış.", "status": "error"})
        await websocket.close()
        return

    job.status = "running"
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def emit(kind: str, **data):
        loop.call_soon_threadsafe(queue.put_nowait, {"type": kind, **data})

    def log(msg: str, status: str = "info"):
        emit("log", msg=msg, status=status)

    def count(n: int):
        job.total = n
        emit("count", total=n)

    def work():
        try:
            run(job.cfg, log, count, job.stop)
        except Exception as exc:  # noqa: BLE001 - kullanıcıya göster
            log(f"Hata: {exc}", "error")
        finally:
            emit("done", total=job.total)

    future = loop.run_in_executor(None, work)
    try:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
            if msg["type"] == "done":
                break
    except Exception:  # istemci koptu
        pass
    finally:
        job.stop.set()          # sekme kapandıysa tarayıcı işini de bitir
        await future
        job.status = "done"
        try:
            await websocket.close()
        except Exception:
            pass


def free_port(start: int, tries: int = 20) -> int:
    """start doluysa sıradaki boş portu bulur (çift tıklayan kullanıcı port düşünmesin)."""
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"{start}-{start + tries - 1} arasında boş port bulunamadı.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--no-browser", action="store_true", help="Arayüzü otomatik açma")
    args = p.parse_args()
    port = free_port(args.port)
    url = f"http://127.0.0.1:{port}"
    print(f"XCleaner çalışıyor: {url}\nKapatmak için bu pencereyi kapat (ya da Ctrl+C).", flush=True)
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
