#!/bin/sh
set -e

# WS_DEMO_MODE is read by workout_selector/web.py at process startup, so
# flipping it means restarting/redeploying this container — not a live
# runtime toggle. In demo mode we also flip the default displayed language
# to EN by rewriting the placeholder script tag index.html always ships
# with (see web/static/index.html) — a one-line, build/startup-time-only
# divergence, kept out of app.js so normal (non-demo) runs are untouched.
if [ "$WS_DEMO_MODE" = "1" ]; then
  sed -i 's/window.WS_DEFAULT_LANG = "ja";/window.WS_DEFAULT_LANG = "en";/' /app/web/static/index.html
fi

exec uvicorn workout_selector.web:app --host 0.0.0.0 --port "${PORT:-8080}"
