import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.orders import router as orders_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

settings = get_settings()

app = FastAPI(title="КОЛЁСА ДЁШЕВО API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)


@app.get("/health")
def health() -> dict[str, str]:
    vk_ready = settings.vk_configured
    return {
        "status": "ok",
        "vk_configured": "yes" if vk_ready else "no",
    }


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"


def _load_product_redirects() -> dict[str, str]:
    redirects_file = STATIC_DIR / "product-redirects.json"
    if not redirects_file.is_file():
        return {}
    try:
        data = json.loads(redirects_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logging.exception("Failed to load product-redirects.json")
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


PRODUCT_REDIRECTS = _load_product_redirects()


def _spa_index() -> FileResponse:
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Frontend is not built")
    return FileResponse(index)


if STATIC_DIR.is_dir():
    if ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    @app.get("/", response_model=None)
    def spa_root() -> FileResponse:
        return _spa_index()

    @app.get("/{full_path:path}", response_model=None)
    def spa_or_static(full_path: str) -> FileResponse | RedirectResponse:
        """Serve real static files; otherwise fall back to SPA index for client routes."""
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        request_path = f"/{full_path}"
        redirect_to = PRODUCT_REDIRECTS.get(request_path)
        if redirect_to:
            return RedirectResponse(url=redirect_to, status_code=301)

        candidate = (STATIC_DIR / full_path).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Not found") from exc

        if candidate.is_file():
            return FileResponse(candidate)

        return _spa_index()
