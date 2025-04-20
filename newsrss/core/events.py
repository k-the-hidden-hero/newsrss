import contextlib
import logging
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from .dependencies import get_config

# Inizializza il logger
logger = logging.getLogger("newsrss")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestore del ciclo di vita dell'applicazione."""
    # Inizializzazione
    # Inizializziamo la configurazione ma non la usiamo direttamente
    get_config()
    logger.info("Inizializzazione dell'applicazione")

    # Yield per passare il controllo all'applicazione
    yield

    # Pulizia
    logger.info("Chiusura dell'applicazione")
