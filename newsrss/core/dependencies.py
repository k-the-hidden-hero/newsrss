import os
from functools import lru_cache
from typing import TypeVar

from fastapi import Depends
from fastapi.templating import Jinja2Templates

from ..models.schemas import RSSFeed
from ..services.rss import RSSService
from .config import AppConfig

# Define type variable for dependency
T = TypeVar("T")

# These singletons will be initialized on first use through cached functions


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Returns the application configuration."""
    settings_file = os.environ.get("NEWSRSS_SETTINGS_FILE")
    return AppConfig(settings_file)


@lru_cache(maxsize=1)
def get_rss_service() -> RSSService:
    """Returns the RSS service."""
    config = get_config()
    return RSSService(
        timeout=config.get_scrape_timeout(), max_retries=config.get_max_retries()
    )


def get_rss_feeds() -> list[RSSFeed]:
    """Returns the list of RSS feeds from configuration."""
    config = get_config()
    # No explicit cast needed anymore as the type is already correct
    return config.get_rss_feeds()


@lru_cache(maxsize=1)
def get_templates() -> Jinja2Templates:
    """Returns Jinja2 templates."""
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates"
    )
    return Jinja2Templates(directory=templates_dir)


# Creating dependencies to avoid B008 errors
config_dependency = Depends(get_config)
rss_service_dependency = Depends(get_rss_service)
rss_feeds_dependency = Depends(get_rss_feeds)
templates_dependency = Depends(get_templates)
