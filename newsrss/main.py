import os
from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends, FastAPI, Path
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import home, playlist
from .core.config import AppConfig
from .core.dependencies import get_config, get_rss_feeds, get_rss_service
from .core.events import lifespan
from .models.schemas import RSSFeed
from .services.rss import RSSService

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
async def m3u_catchall(
    path: Annotated[str, Path()],
    rss_service: Annotated[RSSService, Depends(get_rss_service)],
    feeds: Annotated[list[RSSFeed], Depends(get_rss_feeds)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> Response:
    """Cattura tutti i percorsi che iniziano con /m3u/ e restituisce la playlist."""
    playlist_content = await playlist._generate_playlist(
        rss_service, feeds, config, format_type="m3u"
    )
    return PlainTextResponse(content=playlist_content)


@app.get("/m3u8/{path:path}")
async def m3u8_catchall(
    path: Annotated[str, Path()],
    rss_service: Annotated[RSSService, Depends(get_rss_service)],
    feeds: Annotated[list[RSSFeed], Depends(get_rss_feeds)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> Response:
    """Cattura tutti i percorsi che iniziano con /m3u8/ e restituisce la playlist."""
    playlist_content = await playlist._generate_playlist(
        rss_service, feeds, config, format_type="m3u8"
    )
    return PlainTextResponse(content=playlist_content)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = config.is_debug()

    logger.info(f"Avvio del server su {host}:{port} (reload: {reload})")
    uvicorn.run("newsrss.main:app", host=host, port=port, reload=reload)
