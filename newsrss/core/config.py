import logging
import os

from dynaconf import Dynaconf

from ..models.schemas import RSSFeed

# Logging configuration
logger = logging.getLogger("newsrss")


class AppConfig:
    """
    Manages application configuration using Dynaconf.
    """

    def __init__(self, settings_file: str | None = None):
        """
        Initializes the application configuration.

        Args:
            settings_file: Path to the TOML configuration file.
                           If not specified, environment is used.
        """
        # Current directory where the file is located
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Default values
        self.default_settings_files = [
            os.path.join(current_dir, "settings.toml"),
            os.path.join(current_dir, ".secrets.toml"),
        ]

        # If a file was specified, use it
        if settings_file:
            self.default_settings_files.insert(0, settings_file)

        # Configure the logger before using it
        self.logger = logger

        # Initialize Dynaconf
        self.settings = Dynaconf(
            envvar_prefix="NEWSRSS",
            settings_files=self.default_settings_files,
            environments=False,  # Disable environments
            load_dotenv=True,
        )

        # Debug settings structure
        self.logger.debug(f"Configuration files: {self.default_settings_files}")

        # Configure logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = self.settings.get("log_level", "INFO").upper()
        log_format = self.settings.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Configure root logger
        logging.basicConfig(level=log_level, format=log_format)

        # Set specific logger level
        self.logger.setLevel(log_level)

        self.logger.debug(f"Logging configured at level {log_level}")

    def is_debug(self) -> bool:
        """Returns whether the application is in debug mode."""
        return bool(self.settings.get("debug", False))

    def get_max_scrape_time(self) -> int:
        """Returns the maximum time for scraping feeds."""
        return int(self.settings.get("max_scrape_time", 30))  # Default: 30 seconds

    def get_scrape_timeout(self) -> int:
        """Returns the timeout for HTTP requests during scraping."""
        return int(self.settings.get("scrape_timeout", 20))  # Default: 20 seconds

    def get_max_retries(self) -> int:
        """Returns the maximum number of scraping attempts for each feed."""
        return int(self.settings.get("max_retries", 3))  # Default: 3 attempts

    def get_rss_feeds(self) -> list[RSSFeed]:
        """Returns the list of RSS feeds from configuration."""
        # Access RSS_FEEDS configuration directly
        feeds_config = self.settings.get("rss_feeds", [])

        # Debug found feeds
        self.logger.debug(f"Feed configuration found: {feeds_config}")

        feeds: list[RSSFeed] = []

        # If feeds_config is a list, proceed normally
        if isinstance(feeds_config, list):
            for i, feed_config in enumerate(feeds_config):
                try:
                    # Extract feed data
                    feed_id = feed_config.get("id", i + 1)
                    name = feed_config.get("name", f"Feed {feed_id}")
                    url = feed_config.get("url", "")
                    description = feed_config.get("description", "")
                    timeout = feed_config.get("timeout", self.get_scrape_timeout())

                    if url:  # Add only feeds with valid URL
                        feed = RSSFeed(
                            id=feed_id,
                            name=name,
                            url=url,
                            description=description,
                            timeout=timeout,
                        )
                        feeds.append(feed)
                        self.logger.debug(f"Feed configured: {name} ({url})")
                except Exception as e:
                    self.logger.error(f"Error in feed configuration {i}: {e}")

        self.logger.info(f"Loaded {len(feeds)} RSS feeds")
        return feeds
