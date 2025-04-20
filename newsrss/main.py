import os
from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import FastAPI, Path
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .api import home, playlist
from .core.config import AppConfig
from .core.events import lifespan

# Type variables per le annotazioni dei decoratori
T = TypeVar("T")
DecoratedCallable = Callable[..., T]

# Carica la configurazione
config = AppConfig()
logger = config.logger

# Crea l'applicazione FastAPI
app = FastAPI(
    title="NewsRSS API",
    description="API per la gestione di feed RSS e la generazione di playlist m3u/m3u8",
    version="0.1.0",
    lifespan=lifespan,
    debug=config.is_debug(),
)

# Configura i percorsi statici
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Includi i router
app.include_router(home.router)
app.include_router(playlist.router)


# Gestisci i path m3u/m3u8 anche con sottopercorsi
@app.get("/m3u/{path:path}")
async def m3u_catchall(path: Annotated[str, Path()]) -> Response:
    """Cattura tutti i percorsi che iniziano con /m3u/ e restituisce la playlist."""
    return await playlist.get_m3u_with_path(path)


@app.get("/m3u8/{path:path}")
async def m3u8_catchall(path: Annotated[str, Path()]) -> Response:
    """Cattura tutti i percorsi che iniziano con /m3u8/ e restituisce la playlist."""
    return await playlist.get_m3u8_with_path(path)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = config.is_debug()

    logger.info(f"Avvio del server su {host}:{port} (reload: {reload})")
    uvicorn.run("newsrss.main:app", host=host, port=port, reload=reload)
