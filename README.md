# agent-tax

An agentic tax-filing assistant.

## Overview

This project is being built for the "Build an Agentic Tax-Filing Assistant" hackathon challenge. See [`docs/`](docs/) for the challenge brief and supporting materials.

## Links

- **Live site (Render):** https://agent-tax.onrender.com  _(pending first deploy — Render assigns `<service-name>.onrender.com`; update here if the name is taken and gets a suffix)_
- **Repository (origin):** https://labs.gauntletai.com/michaelhabermas/agent-tax
  - Clone: `git clone https://labs.gauntletai.com/michaelhabermas/agent-tax.git`

## Stack

- **Backend:** Python + FastAPI (uvicorn).
- **LLM:** **OpenRouter** (OpenAI-compatible API), model **`openai/gpt-5.5`** for W-2 vision + tool use. Provider/model are env-configurable (`OPENROUTER_BASE_URL`, `LLM_MODEL`) — swap with zero code changes.
- **PDF:** pypdf fills the provided fillable 2025 Form 1040 (`docs/f1040.pdf`).
- **Frontend:** minimal HTML/CSS/JS chat served by FastAPI (UI polish is explicitly not judged).

## Local run

```bash
cp .env.example .env          # then paste your OPENROUTER_API_KEY into .env
pip install -r requirements.txt
uvicorn agent_tax.main:app --reload --port 8000   # PYTHONPATH=src
```

> `.env` is gitignored and protected; create it from `.env.example` and never commit it.

## Deploy (Render web service)

This is a **web service**, not a static site — it needs a running server for LLM calls, in-memory sessions, and in-memory PDF generation. Deploy via the [`render.yaml`](render.yaml) blueprint: Render → New → Blueprint → this repo, then set the `OPENROUTER_API_KEY` secret. First request after idle is a cold start on the free plan.

## Observability & traceability (Pillar 4)

Behavior is observable, not just promised in a prompt. Each turn emits a **structured trace** — user input → model message → tool calls (name + args) → tool results → computed 1040 lines → decision/next phase — to:

- **stdout** (captured in Render logs), controlled by `LOG_LEVEL`, and
- a **`GET /trace/{session}`** endpoint plus an in-UI trace panel so a judge can watch the harness reason in real time.

Toggle with `TRACE_ENABLED`. See `docs/SPECS.md` §4.7 for the full design.

## Status

Early scaffolding. Deploy config, dependency manifest, and env templates are in place; application code (per `docs/SPECS.md` §A) is next.
