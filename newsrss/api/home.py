import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core.dependencies import (
    config_dependency,
    rss_feeds_dependency,
    rss_service_dependency,
    templates_dependency,
)
from ..models.schemas import RSSFeed
from ..services.rss import RSSService

router = APIRouter()

# Type variables for router annotations
T = TypeVar("T")
DecoratedCallable = Callable[..., T]


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    feeds: list[RSSFeed] = rss_feeds_dependency,
    rss_service: RSSService = rss_service_dependency,
    templates: Jinja2Templates = templates_dependency,
    config: Any = config_dependency,
) -> HTMLResponse:
    """Main endpoint that displays the HTML page with statistics."""
    # Retrieve scraping statistics for each feed
    feeds_stats = []

    # Create a list of tasks for feeds that don't have statistics
    tasks = []
    feeds_to_scrape = []

    for feed in feeds:
        stats = rss_service.get_scrape_stats(feed.id)
        if not stats:
            # No statistics, we need to scrape
            task = asyncio.create_task(rss_service.fetch_feed(feed))
            tasks.append(task)
            feeds_to_scrape.append(feed)

    # If there are feeds to scrape, wait for completion
    if tasks:
        # Use asyncio.wait with timeout to limit waiting time
        max_time = config.get_max_scrape_time()
        done, pending = await asyncio.wait(
            tasks, timeout=max_time, return_when=asyncio.ALL_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

    # Now get updated statistics
    for feed in feeds:
        stats = rss_service.get_scrape_stats(feed.id)

        # Also get the first episode for additional information
        latest_episode = None
        if stats and stats.success:
            latest_episode = await rss_service.get_latest_episode(feed)

        feed_data = {
            "feed_id": feed.id,
            "name": feed.name,
            "description": feed.description,
            "url": feed.url,
            "last_scrape": stats.last_scrape if stats else None,
            "last_duration": stats.last_duration if stats else 0.0,
            "last_episode": stats.last_episode_title if stats else None,
            "success": stats.success if stats else False,
        }

        # Add supplementary information about the episode if available
        if latest_episode:
            # Format duration in a readable format (minutes:seconds)
            minutes = latest_episode.duration // 60
            seconds = latest_episode.duration % 60
            duration_str = f"{minutes}:{seconds:02d}"

            feed_data["episode_url"] = str(latest_episode.url)
            feed_data["episode_duration"] = duration_str

            # Try to get the author from the episode
            # (it might be necessary to add this field to the Episode model)
            # For now we use the feed name as fallback
            feed_data["episode_author"] = getattr(latest_episode, "author", feed.name)

        feeds_stats.append(feed_data)

    return templates.TemplateResponse(
        "index.html", {"request": request, "feeds": feeds_stats}
    )


@router.get("/refresh")
async def refresh(
    feed_id: int | None = Query(
        None,
        description="ID of the specific feed to update, "
        "if omitted updates all feeds",
    ),
    feeds: list[RSSFeed] = rss_feeds_dependency,
    rss_service: RSSService = rss_service_dependency,
    config: Any = config_dependency,
) -> dict[str, Any]:
    """Force scraping of feeds and returns updated statistics."""
    # If a feed_id was specified, filter only that feed
    if feed_id is not None:
        feeds_to_scrape = [feed for feed in feeds if feed.id == feed_id]
    else:
        feeds_to_scrape = feeds

    # Create tasks for each feed to scrape
    tasks = [
        asyncio.create_task(rss_service.fetch_feed(feed)) for feed in feeds_to_scrape
    ]

    # Wait for completion with timeout
    if tasks:
        max_time = config.get_max_scrape_time()
        done, pending = await asyncio.wait(
            tasks, timeout=max_time, return_when=asyncio.ALL_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

    # Prepare response data for all feeds
    feeds_stats = []
    for feed in feeds:
        stats = rss_service.get_scrape_stats(feed.id)

        # Convert date to string for JSON serialization
        last_scrape_str = (
            stats.last_scrape.isoformat() if stats and stats.last_scrape else None
        )

        # Also get the first episode for additional information
        latest_episode = None
        if stats and stats.success:
            latest_episode = await rss_service.get_latest_episode(feed)

        feed_data = {
            "feed_id": feed.id,
            "name": feed.name,
            "description": feed.description,
            "url": str(feed.url),
            "last_scrape": last_scrape_str,
            "last_duration": stats.last_duration if stats else 0.0,
            "last_episode": stats.last_episode_title if stats else None,
            "success": stats.success if stats else False,
        }

        # Add supplementary information about the episode if available
        if latest_episode:
            # Format duration in a readable format (minutes:seconds)
            minutes = latest_episode.duration // 60
            seconds = latest_episode.duration % 60
            duration_str = f"{minutes}:{seconds:02d}"

            feed_data["episode_url"] = str(latest_episode.url)
            feed_data["episode_duration"] = duration_str

            # Try to get the author from the episode
            # (it might be necessary to add this field to the Episode model)
            # For now we use the feed name as fallback
            feed_data["episode_author"] = getattr(latest_episode, "author", feed.name)

        feeds_stats.append(feed_data)

    # Create a variable message depending on the type of update
    update_message = "all feeds" if feed_id is None else f"feed id {feed_id}"

    return {
        "status": "success",
        "message": f"Updated {update_message}",
        "feeds": feeds_stats,
    }
