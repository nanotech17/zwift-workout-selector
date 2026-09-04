# Read-only demo image for Google Cloud Run (see demo-cloudrun-investigation.md).
# Set WS_DEMO_MODE=1 on the Cloud Run service's env vars to switch this same
# image into demo mode (all mutating endpoints return 403, UI hides/disables
# the corresponding controls, default language becomes EN). Leave
# WS_DEMO_MODE unset to run it normally.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY workout_selector/ ./workout_selector/
COPY web/ ./web/
COPY sample_workouts/ ./sample_workouts/

# Bake the demo catalog into the image at build time (Cloud Run instances
# have an ephemeral filesystem, so scanning on every cold start would be
# wasteful and inconsistent across instances).
RUN mkdir -p /app/data \
    && python3 -m workout_selector.cli ingest --dir /app/sample_workouts --db /app/data/catalog.db

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV WS_DB_PATH=/app/data/catalog.db

EXPOSE 8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
