.PHONY: setup lint format typecheck security test coverage clean

# Variabili di progetto
PROJECT_NAME := newsrss
PYTHON := python3
VENV := .venv
PYTHON_VERSION := 3.11
POETRY := poetry

# Colori per output
YELLOW := \033[0;33m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Makefile per il progetto $(PROJECT_NAME)$(NC)"
	@echo ""
	@echo "Comandi disponibili:"
	@echo "  $(YELLOW)help$(NC)        - Mostra questo messaggio di aiuto"
	@echo "  $(YELLOW)setup$(NC)       - Installa tutte le dipendenze e configura pre-commit"
	@echo "  $(YELLOW)lint$(NC)        - Esegue il linting del codice con Ruff"
	@echo "  $(YELLOW)format$(NC)      - Formatta il codice con Black e isort"
	@echo "  $(YELLOW)typecheck$(NC)   - Esegue il controllo statico dei tipi con mypy"
	@echo "  $(YELLOW)security$(NC)    - Esegue la scansione di sicurezza con Gitleaks"
	@echo "  $(YELLOW)quality$(NC)     - Esegue tutti i controlli di qualità"
	@echo "  $(YELLOW)clean$(NC)       - Rimuove file generati e cache"

setup:
	@echo "$(GREEN)Configurazione dell'ambiente di sviluppo...$(NC)"
	$(POETRY) install --with dev
	pre-commit install
	@echo "$(GREEN)Ambiente configurato con successo!$(NC)"

lint:
	@echo "$(GREEN)Esecuzione linting con Ruff...$(NC)"
	$(POETRY) run ruff check .

format:
	@echo "$(GREEN)Formattazione codice con Black e isort...$(NC)"
	$(POETRY) run black .
	$(POETRY) run isort .

typecheck:
	@echo "$(GREEN)Controllo tipi con mypy...$(NC)"
	$(POETRY) run mypy $(PROJECT_NAME)

security:
	@echo "$(GREEN)Scansione di sicurezza con Gitleaks...$(NC)"
	$(POETRY) run gitleaks detect

quality: lint typecheck security test
	@echo "$(GREEN)Tutti i controlli di qualità completati!$(NC)"

clean:
	@echo "$(GREEN)Pulizia file temporanei...$(NC)"
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
