# DECISIONS

This is a Python + FastAPI prototype because the deliverable needs a live web chat, server-side session state, PDF generation, and a simple Render deployment. The deterministic spine is isolated in `core/`: tax math and 1040 filling do not depend on an LLM.

The app fills the provided 2025 Form 1040 with `pypdf` and a checked-in field map. Tax computation uses 2025 constants, the standard deduction, and IRS-style tax-table rounding for incomes under $100k. The supported scope is deliberately narrow: one fake/test W-2, federal Form 1040 only, standard deduction only, no e-filing, no real PII, and no tax advice.

The W-2 tool currently reads text from uploaded PDFs and validates the result with Pydantic. That keeps the demo fast, deterministic, and working without an API key. OpenRouter remains the planned LLM fallback for messy scans, but it is not on the critical path for the hackathon proof.

The harness demonstrates the four required pillars directly: the chat loop carries in-memory session state, tools perform extraction/computation/PDF filling, guardrails enforce scope and a four-question flow under the five-question cap, and `/trace/{session}` plus the UI trace panel expose tool calls, decisions, and blocks.

Deployment target is Render using `render.yaml`. Local fallback is one command after dependency sync: `make run`, then upload `assets/w2_filled_sample_2025.pdf`.
