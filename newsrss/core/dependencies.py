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

# Questi singleton verranno inizializzati al primo utilizzo tramite le funzioni cached


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Restituisce la configurazione dell'applicazione."""
    settings_file = os.environ.get("NEWSRSS_SETTINGS_FILE")
    return AppConfig(settings_file)


@lru_cache(maxsize=1)
def get_rss_service() -> RSSService:
    """Restituisce il servizio RSS."""
    config = get_config()
    return RSSService(
        timeout=config.get_scrape_timeout(), max_retries=config.get_max_retries()
    )


def get_rss_feeds() -> list[RSSFeed]:
    """Restituisce la lista dei feed RSS dalla configurazione."""
    config = get_config()
    # Non è più necessario il cast esplicito perché il tipo è già corretto
    return config.get_rss_feeds()


@lru_cache(maxsize=1)
def get_templates() -> Jinja2Templates:
    """Restituisce i template Jinja2."""
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates"
    )
    return Jinja2Templates(directory=templates_dir)


# Creazione di dipendenze per evitare errori B008
config_dependency = Depends(get_config)
rss_service_dependency = Depends(get_rss_service)
rss_feeds_dependency = Depends(get_rss_feeds)
templates_dependency = Depends(get_templates)
