# agent-tax

An agentic tax-filing assistant.

## Overview

This project is being built for the "Build an Agentic Tax-Filing Assistant" hackathon challenge. See [`docs/`](docs/) for the challenge brief and supporting materials.

## Links

- **Live site (Render):** https://agent-tax-jahv.onrender.com
- **Render dashboard:** https://dashboard.render.com/web/srv-d8u429jaml3c73d4oo10
- **Repository (GitHub mirror, Render deploys from here):** https://github.com/MichaelHabermas/agent-tax
- **Repository (origin / GauntletAI labs):** https://labs.gauntletai.com/michaelhabermas/agent-tax
  - Push to both: `scripts/push-all.sh`

## Stack

- **Backend:** Python + FastAPI (uvicorn).
- **W-2 extraction:** deterministic PDF text extraction for the prototype; OpenRouter is kept as the planned fallback for messy scans.
- **PDF:** pypdf fills the provided fillable 2025 Form 1040 (`assets/f1040.pdf`).
- **Frontend:** minimal HTML/CSS/JS chat served by FastAPI (UI polish is explicitly not judged).

## Local run

```bash
uv sync --extra dev
make run
```

Open http://localhost:8000 and upload `assets/w2_filled_sample_2025.pdf`.
The OpenRouter key is optional for this working prototype; the current W-2 tool reads text PDFs deterministically.

## Deploy (Render web service)

This is a **web service**, not a static site — it needs a running server for in-memory sessions and PDF generation. Deploy via the [`render.yaml`](render.yaml) blueprint. First request after idle is a cold start on the free plan.

## Observability & traceability (Pillar 4)

Behavior is observable, not just promised in a prompt. Each turn emits a **structured trace** — user input → tool calls → tool results → computed 1040 lines → decision/next phase — to:

- **stdout** (captured in Render logs), controlled by `LOG_LEVEL`, and
- a **`GET /trace/{session}`** endpoint plus an in-UI trace panel so a judge can watch the harness reason in real time.

Toggle with `TRACE_ENABLED`. See `docs/SPECS.md` §4.7 for the full design.

## Status

Core prototype is working locally: W-2 upload, stateful chat, guardrails, trace UI, computed 1040, and PDF download. Deploy via `render.yaml` and set `OPENROUTER_API_KEY` only if you add the optional LLM extraction fallback.
