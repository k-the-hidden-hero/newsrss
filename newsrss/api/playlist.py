import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ..core.dependencies import (
    config_dependency,
    rss_feeds_dependency,
    rss_service_dependency,
)
from ..models.schemas import RSSFeed
from ..services.rss import RSSService

router = APIRouter()
logger = logging.getLogger("newsrss")

# Type variables per le annotazioni dei router
T = TypeVar("T")
DecoratedCallable = Callable[..., T]


async def _generate_playlist(
    rss_service: RSSService, feeds: list[RSSFeed], config: Any, format_type: str = "m3u"
) -> str:
    """
    Genera una playlist in formato m3u o m3u8.

    Args:
        rss_service: Servizio RSS per recuperare gli episodi
        feeds: Lista dei feed RSS da cui recuperare gli episodi
        config: Configurazione dell'applicazione
        format_type: Tipo di formato della playlist (m3u o m3u8)

    Returns:
        str: Playlist in formato m3u o m3u8
    """
    # Inizia con l'intestazione della playlist
    if format_type == "m3u8":
        playlist_lines = ["#EXTM3U"]
    else:
        playlist_lines = ["#EXTM3U"]

    # Se non ci sono feed, restituisci solo l'intestazione
    if not feeds:
        logger.warning("Nessun feed configurato per la generazione della playlist")
        # Aggiungi un commento per indicare che non ci sono feed
        playlist_lines.append("#EXTINF:0,Nessun feed configurato")
        playlist_lines.append("http://localhost/dummy.mp3")
        return "\n".join(playlist_lines)

    # Prepara i task per recuperare gli episodi da ogni feed
    tasks = []
    for feed in feeds:
        tasks.append(asyncio.create_task(rss_service.fetch_feed(feed)))

    # Attendi il completamento di tutti i task con timeout
    max_time = config.get_max_scrape_time()
    done, pending = await asyncio.wait(
        tasks, timeout=max_time, return_when=asyncio.ALL_COMPLETED
    )

    # Cancella i task rimanenti
    for task in pending:
        task.cancel()

    # Verifica se abbiamo aggiunto almeno un episodio
    episodes_added = False

    # Ora recupera gli episodi più recenti per ogni feed, rispettando l'ordine dei feed
    for i, feed in enumerate(feeds):
        try:
            episode = await rss_service.get_latest_episode(feed)
            if episode:
                # Formatta la durata in un formato leggibile (minuti:secondi)
                if format_type == "m3u8":
                    # Formato per m3u8
                    playlist_lines.append(
                        f"#EXTINF:{episode.duration},{feed.name} - {episode.title}"
                    )
                else:
                    # Formato per m3u standard
                    playlist_lines.append(
                        f"#EXTINF:{episode.duration},{feed.name} - {episode.title}"
                    )
                playlist_lines.append(str(episode.url))
                episodes_added = True
        except Exception as e:
            feed_name = feed.name if i < len(feeds) else f"feed {i}"
            logger.error(
                f"Errore nel recupero degli episodi per il feed {feed_name}: {e}"
            )

    # Se non è stato aggiunto nessun episodio, aggiungi un dummy
    if not episodes_added:
        logger.warning("Nessun episodio trovato per i feed configurati")
        playlist_lines.append("#EXTINF:0,Nessun episodio trovato")
        playlist_lines.append("http://localhost/dummy.mp3")

    # Unisci le linee della playlist
    playlist_content = "\n".join(playlist_lines)
    return playlist_content


@router.get("/m3u", response_class=PlainTextResponse)
async def get_m3u(
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Genera una playlist m3u."""
    playlist_content = await _generate_playlist(
        rss_service, feeds, config, format_type="m3u"
    )
    return PlainTextResponse(content=playlist_content)


@router.get("/m3u/{path:path}", response_class=PlainTextResponse)
async def get_m3u_with_path(
    path: str,
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Genera una playlist m3u indipendentemente dal percorso richiesto dopo /m3u/."""
    return await get_m3u(rss_service, feeds, config)


@router.get("/m3u8", response_class=PlainTextResponse)
async def get_m3u8(
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Genera una playlist m3u8."""
    playlist_content = await _generate_playlist(
        rss_service, feeds, config, format_type="m3u8"
    )
    return PlainTextResponse(content=playlist_content)


@router.get("/m3u8/{path:path}", response_class=PlainTextResponse)
async def get_m3u8_with_path(
    path: str,
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Genera una playlist m3u8 indipendentemente dal percorso richiesto dopo /m3u8/."""
    return await get_m3u8(rss_service, feeds, config)
