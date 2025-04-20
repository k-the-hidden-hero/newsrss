FROM node:18-slim AS tailwind-builder

WORKDIR /build

# Copy only files needed for Tailwind CSS
COPY package.json tailwind.config.js ./
COPY newsrss/static/css/tailwind ./newsrss/static/css/tailwind/

# Install Tailwind CSS and build CSS
RUN npm install && npm run build:css

# Main stage
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry --no-cache-dir

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Copy source code
COPY newsrss ./newsrss

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Copy compiled CSS from builder
COPY --from=tailwind-builder /build/newsrss/static/css /app/newsrss/static/css

# Environment configuration
ENV PYTHONPATH=/app
ENV NEWSRSS_ENV=production

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Startup command
CMD ["uvicorn", "newsrss.main:app", "--host", "0.0.0.0", "--port", "8000"]
