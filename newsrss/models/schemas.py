from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RSSFeed(BaseModel):
    id: int
    name: str
    description: str
    url: HttpUrl
    timeout: int


class Episode(BaseModel):
    """Rappresenta un episodio di un podcast o un file audio in un feed RSS."""

    feed_id: int
    title: str
    url: HttpUrl
    duration: int
    published: str
    guid: str
    author: str | None = None
    description: str | None = None


class ScrapeStats(BaseModel):
    """Statistiche sullo scraping di un feed."""

    feed_id: int
    success: bool
    last_scrape: datetime | None = None
    last_duration: float = 0.0
    error_message: str | None = None
    retry_count: int = 0
    last_episode_title: str | None = None


class M3UPlaylist(BaseModel):
    """Rappresenta una playlist M3U."""

    episodes: list[Episode]
    total_duration: int
    generated_at: datetime
