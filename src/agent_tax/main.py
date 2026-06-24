"""FastAPI entrypoint (uvicorn target: ``agent_tax.main:app``).

Minimal bootable app: serves a status landing page and a health check so the
Render web service comes up green. It deliberately does NOT instantiate the LLM
client at import time, so the service boots even before ``OPENROUTER_API_KEY`` is
set. Chat/upload/download/trace routes are wired in as the harness lands
(see ``docs/SPECS.md`` §A).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

try:  # local dev convenience; no-op in Render where env vars are injected
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv not installed in some environments
    pass

APP_TITLE = "Agentic Tax-Filing Assistant"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-5.5")
TRACE_ENABLED = os.getenv("TRACE_ENABLED", "true").lower() == "true"

app = FastAPI(title=APP_TITLE)


@app.get("/healthz")
def healthz() -> JSONResponse:
    """Liveness probe used by Render's health check."""
    return JSONResponse(
        {
            "status": "ok",
            "model": LLM_MODEL,
            "api_key_configured": bool(os.getenv("OPENROUTER_API_KEY")),
            "trace_enabled": TRACE_ENABLED,
        }
    )


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Placeholder landing page until the chat UI lands (SPECS F1)."""
    key_ready = "configured" if os.getenv("OPENROUTER_API_KEY") else "NOT set"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{APP_TITLE}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      max-width: 42rem; margin: 4rem auto; padding: 0 1.25rem; line-height: 1.55;
    }}
    h1 {{ font-size: 1.6rem; margin-bottom: .25rem; }}
    .muted {{ opacity: .7; }}
    code {{ background: rgba(127,127,127,.15); padding: .1rem .35rem; border-radius: .3rem; }}
    .card {{ border: 1px solid rgba(127,127,127,.25); border-radius: .6rem; padding: 1rem 1.25rem; margin-top: 1.5rem; }}
    ul {{ padding-left: 1.1rem; }}
  </style>
</head>
<body>
  <h1>{APP_TITLE}</h1>
  <p class="muted">Upload a W-2, answer a few friendly questions, download a completed 2025 Form 1040.</p>
  <div class="card">
    <strong>Service is live.</strong> The chat interface is being wired up.
    <ul>
      <li>Model: <code>{LLM_MODEL}</code> via OpenRouter</li>
      <li>OpenRouter key: <code>{key_ready}</code></li>
      <li>Health: <code>/healthz</code></li>
      <li>Observability: per-turn structured trace &rarr; logs + <code>/trace/{{session}}</code> (Pillar 4)</li>
    </ul>
  </div>
  <p class="muted" style="margin-top:1.5rem;">Prototype with fake/test data only. Not tax advice.</p>
</body>
</html>"""
