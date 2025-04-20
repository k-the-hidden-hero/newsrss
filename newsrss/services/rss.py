import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp
import feedparser

from ..models.schemas import Episode, RSSFeed, ScrapeStats

logger = logging.getLogger("newsrss")

# Constants for comparison
HTTP_STATUS_OK = 200
DURATION_FORMAT_HHMMSS = 3
DURATION_FORMAT_MMSS = 2


class RSSService:
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.scrape_stats: dict[int, ScrapeStats] = {}
        self.episodes_cache: dict[int, list[Episode]] = {}

    async def fetch_feed(
        self, feed: RSSFeed
    ) -> tuple[list[Episode] | None, ScrapeStats]:
        """
        Download the RSS feed and extract episodes.

        Args:
            feed: The RSS feed to download

        Returns:
            Tuple with the list of episodes (or None) and statistics
        """
        start_time = datetime.now()
        stats = ScrapeStats(
            feed_id=feed.id,
            last_scrape=start_time,
            last_duration=0.0,
            success=False,
            last_episode_title=None,
        )

        # Try to download the feed with multiple attempts
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Feed {feed.name}: Attempt {attempt + 1}/{self.max_retries}"
                )
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        str(feed.url), timeout=feed.timeout
                    ) as response:
                        if response.status == HTTP_STATUS_OK:
                            content = await response.text()
                            logger.debug(
                                f"Feed {feed.name}: Content retrieved "
                                f"({len(content)} bytes)"
                            )
                            parsed = feedparser.parse(content)

                            # Extract and format episodes
                            episodes = await self._extract_episodes(parsed, feed.id)

                            # Update cache and statistics
                            if episodes:
                                self.episodes_cache[feed.id] = episodes
                                stats.success = True
                                stats.last_episode_title = episodes[0].title
                                logger.info(
                                    f"Feed {feed.name}: Scraping completed "
                                    f"successfully. Found {len(episodes)} "
                                    f"episodes in {stats.last_duration:.2f} seconds"
                                )
                                stats.last_duration = (
                                    datetime.now() - start_time
                                ).total_seconds()
                                self.scrape_stats[feed.id] = stats
                                return episodes, stats
                            else:
                                logger.warning(f"Feed {feed.name}: No episodes found")
                        else:
                            logger.warning(
                                f"Feed {feed.name}: HTTP response {response.status}"
                            )
            except aiohttp.ClientError as e:
                logger.warning(f"Feed {feed.name}: Request error - {e}")
            except Exception as e:
                logger.error(f"Feed {feed.name}: Unexpected error - {e}")

            # If we got here, there was an error. Retry after a while.
            if attempt < self.max_retries - 1:
                wait_time = 2**attempt  # 1, 2, 4, 8, 16 seconds
                logger.debug(
                    f"Feed {feed.name}: Waiting {wait_time} seconds "
                    f"before next attempt"
                )
                await asyncio.sleep(wait_time)

        # All attempts failed
        try:
            # Try to retrieve episodes from cache
            if feed.id in self.episodes_cache:
                logger.warning(
                    f"Feed {feed.name}: Using cache after "
                    f"{self.max_retries} failed attempts"
                )
                stats.success = False  # Scraping failed even if we use the cache
                stats.last_duration = (datetime.now() - start_time).total_seconds()
                stats.last_episode_title = (
                    self.episodes_cache[feed.id][0].title
                    if self.episodes_cache[feed.id]
                    else None
                )
                self.scrape_stats[feed.id] = stats
                return self.episodes_cache[feed.id], stats
        except Exception as e:
            logger.error(f"Feed {feed.name}: Error accessing cache - {e}")

        stats.last_duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Feed {feed.name}: All {self.max_retries} scraping " f"attempts failed"
        )
        self.scrape_stats[feed.id] = stats
        return None, stats

    async def _extract_episodes(self, parsed_feed: Any, feed_id: int) -> list[Episode]:
        """Extract episodes from the parsed feed."""
        episodes: list[Episode] = []

        # Check if there are entries in the feed
        if not hasattr(parsed_feed, "entries") or not parsed_feed.entries:
            return episodes

        # Extract information from feed elements
        for entry in parsed_feed.entries:
            try:
                # Find the episode URL
                enclosure = next(
                    (e for e in entry.get("enclosures", []) if "url" in e), None
                )
                if not enclosure:
                    continue

                # Determine episode duration
                duration = 0
                try:
                    # Look for duration tag
                    duration_str = entry.get("itunes_duration", "0:0")
                    if duration_str:
                        # Handle different duration formats (HH:MM:SS, MM:SS, SS)
                        parts = duration_str.split(":")
                        if len(parts) == DURATION_FORMAT_HHMMSS:  # HH:MM:SS
                            duration = (
                                int(parts[0]) * 3600
                                + int(parts[1]) * 60
                                + int(parts[2])
                            )
                        elif len(parts) == DURATION_FORMAT_MMSS:  # MM:SS
                            duration = int(parts[0]) * 60 + int(parts[1])
                        else:  # SS or other format
                            duration = (
                                int(duration_str) if duration_str.isdigit() else 0
                            )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing duration: {e}")
                    duration = 0

                # Create Episode object
                episode = Episode(
                    feed_id=feed_id,
                    title=entry.get("title", "No title"),
                    url=enclosure.get("url", ""),
                    duration=duration,
                    published=entry.get("published", ""),
                    guid=entry.get("id", ""),
                )
                episodes.append(episode)
            except Exception as e:
                logger.error(f"Error extracting episode: {e}")

        # Sort episodes by publication date (most recent first)
        episodes.sort(key=lambda x: x.published, reverse=True)
        return episodes

    def get_scrape_stats(self, feed_id: int) -> ScrapeStats | None:
        """Return scraping statistics for a feed."""
        return self.scrape_stats.get(feed_id)

    async def get_latest_episode(self, feed: RSSFeed) -> Episode | None:
        """Return the most recent episode for a feed."""
        if self.episodes_cache.get(feed.id):
            return self.episodes_cache[feed.id][0]
        episodes, _ = await self.fetch_feed(feed)
        if episodes:
            return episodes[0]
        return None
