import logging
import os

from dynaconf import Dynaconf

from ..models.schemas import RSSFeed

# Configurazione logging
logger = logging.getLogger("newsrss")


class AppConfig:
    """
    Gestisce la configurazione dell'applicazione utilizzando Dynaconf.
    """

    def __init__(self, settings_file: str | None = None):
        """
        Inizializza la configurazione dell'applicazione.

        Args:
            settings_file: Percorso del file di configurazione TOML.
                           Se non specificato, viene utilizzato l'ambiente.
        """
        # Directory corrente dove si trova il file
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Valori di default
        self.default_settings_files = [
            os.path.join(current_dir, "settings.toml"),
            os.path.join(current_dir, ".secrets.toml"),
        ]

        # Se è stato specificato un file, lo utilizziamo
        if settings_file:
            self.default_settings_files.insert(0, settings_file)

        # Configura il logger prima di usarlo
        self.logger = logger

        # Inizializza Dynaconf
        self.settings = Dynaconf(
            envvar_prefix="NEWSRSS",
            settings_files=self.default_settings_files,
            environments=False,  # Disabilita gli ambienti
            load_dotenv=True,
        )

        # Debug della struttura delle impostazioni
        self.logger.debug(f"File di configurazione: {self.default_settings_files}")

        # Configura il logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configura il logging in base alle impostazioni."""
        log_level = self.settings.get("log_level", "INFO").upper()
        log_format = self.settings.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Configura il logger root
        logging.basicConfig(level=log_level, format=log_format)

        # Imposta il livello del logger specifico
        self.logger.setLevel(log_level)

        self.logger.debug(f"Logging configurato al livello {log_level}")

    def is_debug(self) -> bool:
        """Restituisce se l'applicazione è in modalità debug."""
        return bool(self.settings.get("debug", False))

    def get_max_scrape_time(self) -> int:
        """Restituisce il tempo massimo per lo scraping dei feed."""
        return int(self.settings.get("max_scrape_time", 30))  # Default: 30 secondi

    def get_scrape_timeout(self) -> int:
        """Restituisce il timeout per le richieste HTTP durante lo scraping."""
        return int(self.settings.get("scrape_timeout", 20))  # Default: 20 secondi

    def get_max_retries(self) -> int:
        """Restituisce il numero massimo di tentativi di scraping per ogni feed."""
        return int(self.settings.get("max_retries", 3))  # Default: 3 tentativi

    def get_rss_feeds(self) -> list[RSSFeed]:
        """Restituisce la lista dei feed RSS dalla configurazione."""
        # Accedi direttamente alla configurazione RSS_FEEDS
        feeds_config = self.settings.get("rss_feeds", [])

        # Debug dei feed trovati
        self.logger.debug(f"Configurazione feed trovata: {feeds_config}")

        feeds: list[RSSFeed] = []

        # Se feeds_config è una lista, procedi normalmente
        if isinstance(feeds_config, list):
            for i, feed_config in enumerate(feeds_config):
                try:
                    # Estrai i dati dal feed
                    feed_id = feed_config.get("id", i + 1)
                    name = feed_config.get("name", f"Feed {feed_id}")
                    url = feed_config.get("url", "")
                    description = feed_config.get("description", "")
                    timeout = feed_config.get("timeout", self.get_scrape_timeout())

                    if url:  # Aggiungi solo feed con URL valido
                        feed = RSSFeed(
                            id=feed_id,
                            name=name,
                            url=url,
                            description=description,
                            timeout=timeout,
                        )
                        feeds.append(feed)
                        self.logger.debug(f"Feed configurato: {name} ({url})")
                except Exception as e:
                    self.logger.error(f"Errore nella configurazione del feed {i}: {e}")

        self.logger.info(f"Caricati {len(feeds)} feed RSS")
        return feeds
