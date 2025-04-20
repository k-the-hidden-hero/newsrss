# newsrss

[![Code Quality](https://github.com/k-the-hidden-hero/newsrss/actions/workflows/code-quality.yml/badge.svg)](https://github.com/k-the-hidden-hero/newsrss/actions/workflows/code-quality.yml)
[![Build and Release](https://github.com/k-the-hidden-hero/newsrss/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/k-the-hidden-hero/newsrss/actions/workflows/build-and-release.yml)
[![License: WTFPL](https://img.shields.io/badge/License-WTFPL-brightgreen.svg)](http://www.wtfpl.net/about/)
[![Docker Pulls](https://img.shields.io/docker/pulls/ghcr.io/k-the-hidden-hero/newsrss)](https://github.com/k-the-hidden-hero/newsrss/pkgs/container/newsrss)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)


An API that provides always up-to-date M3U and M3U8 playlists of audio files from RSS feeds. Designed to run in containerized environments such as Kubernetes or Cloud Run.

## Features

- REST API based on FastAPI
- Generates M3U and M3U8 playlists from multiple RSS feeds
- Web dashboard with feed statistics
- Flexible configuration via TOML or environment variables
- Fully containerized and optimized for cloud environments

## Container Image

The container image is available on GitHub Container Registry:

```bash
docker pull ghcr.io/k-the-hidden-hero/newsrss:latest
```

### Available Tags

- `latest`: latest stable release
- `x.y.z`: specific version (e.g. `1.0.0`)
- `devel`: development version (from development branch)
- `prerelease`: latest pre-release

## Quick Usage

```bash
docker run -p 8000:8000 -v /path/to/settings.toml:/app/settings.toml ghcr.io/k-the-hidden-hero/newsrss:latest
```

## Configuration

The application can be configured using a TOML file or environment variables.

### TOML Configuration Example

```toml
# Base configuration
debug = false
log_level = "info"
max_scrape_time = 60
max_retries = 5
scrape_timeout = 40

# RSS feeds configuration
[[rss_feeds]]
id = 1
name = "Radio24 News"
description = "Radio 24 News"
url = "https://www.spreaker.com/show/4311383/episodes/feed"
timeout = 40

[[rss_feeds]]
id = 4
name = "RTL 102.5"
description = "RTL 102.5 Hourly News"
url = "https://rss.rtl.it/podcast/giornale-orario/?mediaType=201"
timeout = 40

[[rss_feeds]]
id = 5
name = "Radio Capital News"
description = "Capital News Hourly Report"
url = "https://www.capital.it/api/pub/v1/rss/google-assistant/833%22%20type=%22rss%22%20text=%22Capital%20News%20GR%22"
timeout = 40

```

### Environment Variables

- `NEWSRSS_DEBUG`: enables debug logging
- `NEWSRSS_MAX_TIMEOUT`: maximum timeout for playlist generation (seconds)
- `NEWSRSS_RETRY_COUNT`: maximum number of retry attempts for feed retrieval
- `NEWSRSS_SCRAPE_TIMEOUT`: timeout for retrieving a single feed (seconds)
- `NEWSRSS_CONFIG_PATH`: path to the TOML configuration file

## API Endpoints

- `/`: Web dashboard with RSS feed statistics
- `/m3u` or `/m3u/*`: Returns the playlist in M3U format
- `/m3u8` or `/m3u8/*`: Returns the playlist in M3U8 format

## Development

### Prerequisites

- Python 3.11+
- Poetry
- Node.js and npm (for Tailwind CSS)

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/k-the-hidden-hero/newsrss.git
cd newsrss

# Install dependencies with Poetry
poetry install

# Install npm dependencies for Tailwind CSS
npm install

# Compile CSS
npm run build:css

# Start the application in development mode
poetry run uvicorn newsrss.main:app --reload
```

## ArgoCD Application example:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: newsrss
  namespace: argocd
spec:
  project: default
  source:
    chart: application
    repoURL: https://stakater.github.io/stakater-charts
    targetRevision: 6.0.2
    helm:
      releaseName: newsrss
      valuesObject:
        applicationName: newsrss

        deployment:
          image:
            repository: ghcr.io/k-the-hidden-hero/newsrss
            tag: 0.4.0

          env:
            NEWSRSS_DEBUG:
              value: "false"
            NEWSRSS_MAX_TIMEOUT:
              value: "60"
            NEWSRSS_RETRY_COUNT:
              value: "5"
            NEWSRSS_SCRAPE_TIMEOUT:
              value: "40"
            NEWSRSS_CONFIG_PATH:
              value: "/app/settings.toml"

          volumes:
            config:
              configMap:
                name: newsrss-config

          volumeMounts:
            config:
              mountPath: /app/settings.toml
              subPath: settings.toml

          readinessProbe:
            enabled: true
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 0
            periodSeconds: 5

          livenessProbe:
            enabled: true
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 300

          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi

          containerSecurityContext:
            readOnlyRootFilesystem: false
            runAsNonRoot: false

        service:
          enabled: true
          ports:
          - name: http
            port: 80
            targetPort: 8000
            protocol: TCP

        configMap:
          enabled: true
          files:
            config:
              settings.toml: |
                # Base configuration
                debug = false
                log_level = "info"
                max_scrape_time = 60
                max_retries = 5
                scrape_timeout = 40

                # RSS feeds configuration
                [[rss_feeds]]
                id = 1
                name = "Radio24 News"
                description = "Radio 24 News"
                url = "https://www.spreaker.com/show/4311383/episodes/feed"
                timeout = 40

                [[rss_feeds]]
                id = 4
                name = "RTL 102.5"
                description = "RTL 102.5 Hourly News"
                url = "https://rss.rtl.it/podcast/giornale-orario/?mediaType=201"
                timeout = 40

                [[rss_feeds]]
                id = 5
                name = "Radio Capital News"
                description = "Capital News Hourly Report"
                url = "https://www.capital.it/api/pub/v1/rss/google-assistant/833%22%20type=%22rss%22%20text=%22Capital%20News%20GR%22"
                timeout = 40

        ingress:
          enabled: true
          className: nginx
          annotations:
            cert-manager.io/cluster-issuer: cloudflare
          hosts:
            - host: newsrss.mydomain.dev
              paths:
                - path: /
                  pathType: Prefix
          tls:
            - hosts:
              - newsrss.mydomain.dev
              secretName: newsrss-ingress-tls

  destination:
    server: https://kubernetes.default.svc
    namespace: newsrss

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: true
    syncOptions:
    - CreateNamespace=true
  ignoreDifferences:
  - group: "apps"
    kind: Deployment
    jsonPointers:
    - /spec/template/spec/hostUsers
  - group: ""
    kind: Secret
    jsonPointers:
    - /data
    - /stringData

```
