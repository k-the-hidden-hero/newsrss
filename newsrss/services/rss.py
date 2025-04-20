import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp
import feedparser

from ..models.schemas import Episode, RSSFeed, ScrapeStats

logger = logging.getLogger("newsrss")

# Costanti per la comparazione
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
        Scarica il feed RSS e ne estrae gli episodi.

        Args:
            feed: Il feed RSS da scaricare

        Returns:
            Tuple con la lista di episodi (o None) e statistiche
        """
        start_time = datetime.now()
        stats = ScrapeStats(
            feed_id=feed.id,
            last_scrape=start_time,
            last_duration=0.0,
            success=False,
            last_episode_title=None,
        )

        # Prova a scaricare il feed con più tentativi
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Feed {feed.name}: Tentativo {attempt + 1}/{self.max_retries}"
                )
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        str(feed.url), timeout=feed.timeout
                    ) as response:
                        if response.status == HTTP_STATUS_OK:
                            content = await response.text()
                            logger.debug(
                                f"Feed {feed.name}: Contenuto recuperato "
                                f"({len(content)} bytes)"
                            )
                            parsed = feedparser.parse(content)

                            # Estrai e formatta gli episodi
                            episodes = await self._extract_episodes(parsed, feed.id)

                            # Aggiorna la cache e le statistiche
                            if episodes:
                                self.episodes_cache[feed.id] = episodes
                                stats.success = True
                                stats.last_episode_title = episodes[0].title
                                logger.info(
                                    f"Feed {feed.name}: Scraping completato "
                                    f"con successo. Trovati {len(episodes)} "
                                    f"episodi in {stats.last_duration:.2f} secondi"
                                )
                                stats.last_duration = (
                                    datetime.now() - start_time
                                ).total_seconds()
                                self.scrape_stats[feed.id] = stats
                                return episodes, stats
                            else:
                                logger.warning(
                                    f"Feed {feed.name}: Nessun episodio trovato"
                                )
                        else:
                            logger.warning(
                                f"Feed {feed.name}: Risposta HTTP {response.status}"
                            )
            except aiohttp.ClientError as e:
                logger.warning(f"Feed {feed.name}: Errore nella richiesta - {e}")
            except Exception as e:
                logger.error(f"Feed {feed.name}: Errore imprevisto - {e}")

            # Se siamo arrivati qui, c'è stato un errore. Riprova dopo un po'.
            if attempt < self.max_retries - 1:
                wait_time = 2**attempt  # 1, 2, 4, 8, 16 secondi
                logger.debug(
                    f"Feed {feed.name}: Attesa di {wait_time} secondi "
                    f"prima del prossimo tentativo"
                )
                await asyncio.sleep(wait_time)

        # Tutti i tentativi sono falliti
        try:
            # Prova a recuperare gli episodi dalla cache
            if feed.id in self.episodes_cache:
                logger.warning(
                    f"Feed {feed.name}: Utilizzo cache dopo "
                    f"{self.max_retries} tentativi falliti"
                )
                stats.success = False  # Lo scraping è fallito anche se usiamo la cache
                stats.last_duration = (datetime.now() - start_time).total_seconds()
                stats.last_episode_title = (
                    self.episodes_cache[feed.id][0].title
                    if self.episodes_cache[feed.id]
                    else None
                )
                self.scrape_stats[feed.id] = stats
                return self.episodes_cache[feed.id], stats
        except Exception as e:
            logger.error(f"Feed {feed.name}: Errore nell'accesso alla cache - {e}")

        stats.last_duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Feed {feed.name}: Tutti i {self.max_retries} tentativi "
            f"di scraping sono falliti"
        )
        self.scrape_stats[feed.id] = stats
        return None, stats

    async def _extract_episodes(self, parsed_feed: Any, feed_id: int) -> list[Episode]:
        """Estrae gli episodi dal feed parsato."""
        episodes: list[Episode] = []

        # Verifica che ci siano voci nel feed
        if not hasattr(parsed_feed, "entries") or not parsed_feed.entries:
            return episodes

        # Estrai le informazioni dagli elementi del feed
        for entry in parsed_feed.entries:
            try:
                # Trova l'URL dell'episodio
                enclosure = next(
                    (e for e in entry.get("enclosures", []) if "url" in e), None
                )
                if not enclosure:
                    continue

                # Determina la durata dell'episodio
                duration = 0
                try:
                    # Cerca il tag di durata
                    duration_str = entry.get("itunes_duration", "0:0")
                    if duration_str:
                        # Gestisci diversi formati di durata (HH:MM:SS, MM:SS, SS)
                        parts = duration_str.split(":")
                        if len(parts) == DURATION_FORMAT_HHMMSS:  # HH:MM:SS
                            duration = (
                                int(parts[0]) * 3600
                                + int(parts[1]) * 60
                                + int(parts[2])
                            )
                        elif len(parts) == DURATION_FORMAT_MMSS:  # MM:SS
                            duration = int(parts[0]) * 60 + int(parts[1])
                        else:  # SS o altro formato
                            duration = (
                                int(duration_str) if duration_str.isdigit() else 0
                            )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Errore nel parsing della durata: {e}")
                    duration = 0

                # Crea l'oggetto Episode
                episode = Episode(
                    feed_id=feed_id,
                    title=entry.get("title", "Senza titolo"),
                    url=enclosure.get("url", ""),
                    duration=duration,
                    published=entry.get("published", ""),
                    guid=entry.get("id", ""),
                )
                episodes.append(episode)
            except Exception as e:
                logger.error(f"Errore nell'estrazione dell'episodio: {e}")

        # Ordina gli episodi per data di pubblicazione (il più recente per primo)
        episodes.sort(key=lambda x: x.published, reverse=True)
        return episodes

    def get_scrape_stats(self, feed_id: int) -> ScrapeStats | None:
        """Restituisce le statistiche di scraping per un feed."""
        return self.scrape_stats.get(feed_id)

    async def get_latest_episode(self, feed: RSSFeed) -> Episode | None:
        """Restituisce l'episodio più recente per un feed."""
        if self.episodes_cache.get(feed.id):
            return self.episodes_cache[feed.id][0]
        episodes, _ = await self.fetch_feed(feed)
        if episodes:
            return episodes[0]
        return None
