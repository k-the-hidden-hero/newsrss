import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from ..core.dependencies import (
    config_dependency,
    rss_feeds_dependency,
    rss_service_dependency,
)
from ..models.schemas import RSSFeed
from ..services.rss import RSSService

router = APIRouter()
logger = logging.getLogger("newsrss")

# Type variables for router annotations
T = TypeVar("T")
DecoratedCallable = Callable[..., T]


async def _generate_m3u_content(
    rss_service: RSSService, feeds: list[RSSFeed], config: Any, format_type: str = "m3u"
) -> str:
    """Generate M3U or M3U8 playlist content."""
    playlist_lines = ["#EXTM3U"]

    # If there are no feeds, return just the header
    if not feeds:
        logger.warning("No feeds configured for playlist generation")
        # Add a comment to indicate there are no feeds
        playlist_lines.append("#EXTINF:0,No feeds configured")
        playlist_lines.append("http://localhost/dummy.mp3")
        return "\n".join(playlist_lines)

    # Retrieve episodes
    episodes_added = False
    for i, feed in enumerate(feeds):
        try:
            episode = await rss_service.get_latest_episode(feed)
            if episode:
                # Format for m3u/m3u8
                playlist_lines.append(
                    f"#EXTINF:{episode.duration},{feed.name} - {episode.title}"
                )
                playlist_lines.append(str(episode.url))
                episodes_added = True
        except Exception as e:
            feed_name = feed.name if i < len(feeds) else f"feed {i}"
            logger.error(f"Error retrieving episodes for feed {feed_name}: {e}")

    # If no episodes were added, add a dummy
    if not episodes_added:
        logger.warning("No episodes found for configured feeds")
        playlist_lines.append("#EXTINF:0,No episodes found")
        playlist_lines.append("http://localhost/dummy.mp3")

    # Join playlist lines
    return "\n".join(playlist_lines)


async def _generate_hasensor_content(
    rss_service: RSSService, feeds: list[RSSFeed], config: Any
) -> dict[str, Any]:
    """Generate JSON content for hasensor format."""
    episodes_data = []
    episodes_added = False

    # Retrieve episodes for each feed
    for i, feed in enumerate(feeds):
        try:
            episode = await rss_service.get_latest_episode(feed)
            if episode:
                episodes_data.append(
                    {
                        "feed_id": feed.id,
                        "feed_name": feed.name,
                        "feed_description": feed.description,
                        "episode_title": episode.title,
                        "episode_url": str(episode.url),
                        "duration": episode.duration,
                    }
                )
                episodes_added = True
        except Exception as e:
            feed_name = feed.name if i < len(feeds) else f"feed {i}"
            logger.error(f"Error retrieving episodes for feed {feed_name}: {e}")

    # Return appropriate JSON response
    if not episodes_added:
        logger.warning("No episodes found for configured feeds")
        return {"status": "error", "message": "No episodes found", "episodes": []}
    return {"status": "success", "episodes": episodes_data}


async def _generate_playlist(
    rss_service: RSSService, feeds: list[RSSFeed], config: Any, format_type: str = "m3u"
) -> str | dict[str, Any]:
    """
    Generate a playlist in m3u, m3u8, or hasensor format.

    Args:
        rss_service: RSS service to retrieve episodes
        feeds: List of RSS feeds to retrieve episodes from
        config: Application configuration
        format_type: Playlist format type (m3u, m3u8, or hasensor)

    Returns:
        Union[str, Dict[str, Any]]: Playlist content as string or JSON data
    """
    # Prepare tasks to retrieve episodes from each feed
    tasks = []
    for feed in feeds:
        tasks.append(asyncio.create_task(rss_service.fetch_feed(feed)))

    # Wait for all tasks to complete with timeout
    max_time = config.get_max_scrape_time()
    done, pending = await asyncio.wait(
        tasks, timeout=max_time, return_when=asyncio.ALL_COMPLETED
    )

    # Cancel remaining tasks
    for task in pending:
        task.cancel()

    # Generate appropriate content based on format type
    if format_type == "hasensor":
        return await _generate_hasensor_content(rss_service, feeds, config)
    else:
        return await _generate_m3u_content(rss_service, feeds, config, format_type)


@router.get("/m3u", response_class=PlainTextResponse)
async def get_m3u(
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Generate an m3u playlist."""
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
    """Generate an m3u playlist regardless of the requested path after /m3u/."""
    return await get_m3u(rss_service, feeds, config)


@router.get("/m3u8", response_class=PlainTextResponse)
async def get_m3u8(
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Generate an m3u8 playlist."""
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
    """Generate an m3u8 playlist regardless of the requested path after /m3u8/."""
    return await get_m3u8(rss_service, feeds, config)


@router.get("/hasensor", response_class=JSONResponse)
async def get_hasensor(
    rss_service: RSSService = rss_service_dependency,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    config: Any = config_dependency,
) -> Response:
    """Generate a JSON response with the latest episodes from all feeds."""
    playlist_content = await _generate_playlist(
        rss_service, feeds, config, format_type="hasensor"
    )
    return JSONResponse(content=playlist_content)
