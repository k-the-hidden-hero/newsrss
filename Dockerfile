FROM node:18-slim AS tailwind-builder

WORKDIR /build

# Copia solo i file necessari per Tailwind CSS
COPY package.json tailwind.config.js ./
COPY newsrss/static/css/tailwind ./newsrss/static/css/tailwind/

# Installazione di Tailwind CSS e build del CSS
RUN npm install && npm run build:css

# Stage principale
FROM python:3.11-slim

WORKDIR /app

# Installazione delle dipendenze Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copia del CSS compilato dal builder
COPY --from=tailwind-builder /build/newsrss/static/css /app/newsrss/static/css

# Copia del resto del codice
COPY newsrss /app/newsrss

# Configurazione dell'ambiente
ENV PYTHONPATH=/app
ENV NEWSRSS_ENV=production

# Creazione di un utente non-root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Esposizione della porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Comando di avvio
CMD ["uvicorn", "newsrss.main:app", "--host", "0.0.0.0", "--port", "8000"]
