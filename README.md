# NewsM3U

![Build and Release](https://github.com/k-the-hidden-hero/newsm3u/actions/workflows/build-and-release.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/ghcr.io/k-the-hidden-hero/newsm3u)

Un'API che fornisce playlist M3U e M3U8 sempre aggiornate di file audio da feed RSS. Progettata per essere eseguita in ambienti containerizzati come Kubernetes o Cloud Run.

## Funzionalità

- API REST basata su FastAPI
- Genera playlist M3U e M3U8 da feed RSS multipli
- Dashboard web con statistiche sui feed
- Configurazione flessibile tramite TOML o variabili d'ambiente
- Perfettamente containerizzata e ottimizzata per ambienti cloud

## Immagine Container

L'immagine container è disponibile su GitHub Container Registry:

```bash
docker pull ghcr.io/k-the-hidden-hero/newsm3u:latest
```

### Tag disponibili

- `latest`: ultima versione stabile rilasciata
- `x.y.z`: versione specifica (es. `1.0.0`)
- `devel`: versione di sviluppo (dal branch development)
- `prerelease`: ultima pre-release

## Utilizzo Rapido

```bash
docker run -p 8000:8000 -v /path/to/config.toml:/app/config.toml ghcr.io/k-the-hidden-hero/newsm3u:latest
```

## Configurazione

L'applicazione può essere configurata tramite file TOML o variabili d'ambiente.

### Esempio di configurazione TOML

```toml
[app]
debug = true
max_timeout = 30
retry_count = 3
scrape_timeout = 20

[[feeds]]
id = 1
name = "Radio RAI 1"
description = "Giornale Radio RAI 1"
url = "https://www.raiplaysound.it/programmi/gr1.xml"
timeout = 15

[[feeds]]
id = 2
name = "Radio RAI 2"
description = "Giornale Radio RAI 2"
url = "https://www.raiplaysound.it/programmi/gr2.xml"
timeout = 15
```

### Variabili d'Ambiente

- `NEWSRSS_DEBUG`: abilita il logging di debug
- `NEWSRSS_MAX_TIMEOUT`: timeout massimo per la generazione delle playlist (secondi)
- `NEWSRSS_RETRY_COUNT`: numero massimo di tentativi per il recupero dei feed
- `NEWSRSS_SCRAPE_TIMEOUT`: timeout per il recupero di un singolo feed (secondi)
- `NEWSRSS_CONFIG_PATH`: percorso del file di configurazione TOML

## Endpoints API

- `/`: Dashboard web con statistiche sui feed RSS
- `/m3u` o `/m3u/*`: Restituisce la playlist in formato M3U
- `/m3u8` o `/m3u8/*`: Restituisce la playlist in formato M3U8

## Sviluppo

### Prerequisiti

- Python 3.11+
- Poetry
- Node.js e npm (per Tailwind CSS)

### Setup dell'ambiente di sviluppo

```bash
# Clona il repository
git clone https://github.com/k-the-hidden-hero/newsm3u.git
cd newsm3u

# Installa le dipendenze con Poetry
poetry install

# Installa le dipendenze npm per Tailwind CSS
npm install

# Compila il CSS
npm run build:css

# Avvia l'applicazione in modalità sviluppo
poetry run uvicorn newsrss.main:app --reload
```

### Skaffold per sviluppo Kubernetes

```bash
skaffold dev
```

## Licenza

MIT

## Controlli di Qualità del Codice

Per garantire la qualità e la sicurezza del codice, questo progetto utilizza diversi strumenti automatizzati:

### Strumenti di Formattazione e Linting

- **Black**: Formattatore automatico del codice Python
- **isort**: Organizzazione automatica delle importazioni
- **Ruff**: Linter Python veloce che include regole da Flake8, Pylint e altri
- **mypy**: Controllo statico dei tipi in Python

### Sicurezza

- **Gitleaks**: Scansione del repository per individuare eventuali credenziali o token esposti

### Come Utilizzare gli Strumenti

1. **Installazione delle dipendenze di sviluppo**:
   ```bash
   poetry install --with dev
   ```

2. **Attivazione di pre-commit**:
   ```bash
   pre-commit install
   ```

3. **Esecuzione manuale dei controlli**:
   ```bash
   # Formattazione con Black
   black .

   # Organizzazione delle importazioni
   isort .

   # Linting con Ruff
   ruff check .

   # Controllo dei tipi
   mypy newsrss

   # Scansione di sicurezza
   gitleaks detect
   ```

4. **Workflow CI/CD**:
   Questi controlli vengono eseguiti automaticamente su GitHub Actions ad ogni push o pull request.

### Configurazione

- Le configurazioni di tutti gli strumenti si trovano nel file `pyproject.toml`
- La configurazione di pre-commit è definita in `.pre-commit-config.yaml`
- Le regole personalizzate per Gitleaks sono definite in `.gitleaks.toml`
