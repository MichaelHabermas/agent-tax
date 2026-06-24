# SPECS — Agentic Tax-Filing Assistant (2025 Form 1040)

> Spec sheet for the hackathon build.
> **Part 1** — *hard* requirements (non-negotiable, lifted from the brief) + an **atomized,
> brief-cited traceability matrix** (§1.7) that proves nothing is missed.
> **Part 2** — our **decisions** (§2), **verified facts** (§3), and the *soft / implied* requirements
> the hard ones force into existence (§4).
> **Part 3** — **architecture & file structure** (§A), the ~1-hour build plan, risks, scope, assumptions.
>
> Source brief: [`docs/Hackathon Challenge — Build an Agentic Tax-Filing Assistant.md`](Hackathon%20Challenge%20—%20Build%20an%20Agentic%20Tax-Filing%20Assistant.md)
> — cited below as **Brief L\<n\>** (line numbers in that markdown file).

---

## 0. TL;DR

Build a **web chat** where a person uploads a single W-2, answers **≤5 friendly questions**, and
downloads a **completed 2025 IRS Form 1040**. The system visibly demonstrates four harness pillars —
**chat loop, tools, guardrails, observation** — and is **deployed to a public URL** (Render or
comparable free host). Judged first on *harness quality*, then *does it actually work end-to-end*,
then *conversation quality*, then *soundness of decisions*. UI polish is explicitly **not** judged.

Works for **any** single W-2 — **nothing is hardcoded to the sample taxpayer**. Built **SOLID / DRY**
with **single-source-of-truth** config: tax constants, the 1040 field map, and the sample fixture
each live in exactly one place (§A).

**Locked decisions (→ §2):** Python + FastAPI · Claude (Sonnet 4.6 default, Opus 4.8 fallback) ·
W-2 read by **Claude vision → schema-validated `W2` object** · 1040 filled with **pypdf** on the provided
`docs/f1040.pdf` · tax via the **exact IRS Tax Table** · guardrails in **code + schema** · deploy to **Render**.

---

# PART 1 — HARD REQUIREMENTS (non-negotiable)

## 1.1 The Four Pillars (required — the highest-weighted judging axis)

A judge must point at code **and** the running system and see each pillar working. "It's in the
prompt" is explicitly weaker than "it's enforced and visible." *(Brief L17–29.)*

| # | Pillar | The bar | Our concrete realization (→ §4, §A) |
|---|--------|---------|-------------------------------------|
| 1 | **Chat loop** | Conversational loop that **carries state across turns**. | Session-scoped state machine; each turn appends history and advances a phase. |
| 2 | **Tools** | **Real actions** via defined tools — at minimum, produce the filled return. | `extract_w2`, `compute_1040`, `fill_1040_pdf` as schema-typed tools. |
| 3 | **Guardrails** | Keep it **on-task, safe, bounded**: validate inputs, respect limits. | Pydantic schemas, plausibility checks, scope refusals, hard ≤5 counter in code. |
| 4 | **Observation** | Behavior **observable**: what it did, decided, acted on. | Structured per-turn trace → logs + UI panel. |

## 1.2 Definition of Done (end-result checklist) — *Brief L32–42*

- [ ] **Web-based chat** a user can interact with.
- [x] Realistic fake W-2 supplied for testing — `docs/w2_filled_sample_2025.pdf` ✅ (user supplies/uploads at runtime).
- [ ] Agent asks **no more than 5 questions**.
- [ ] Conversation feels **warm and human** *(explicitly part of the bar)*.
- [ ] Agent fills a **2025 IRS Form 1040** from the W-2 + answers.
- [ ] Completed 1040 is **downloadable as a file**.
- [ ] **Deployed to a public URL** on Render or comparable free host.

## 1.3 Fixed constraints (do not change) — *Brief L46–58*

- **Form:** U.S. Federal **Form 1040**, **tax year 2025**.
- **Taxpayer:** a single W-2 (sample ~$48k — see §8); app generalizes to **any** single W-2.
- **Filing status:** must handle **single, MFJ, etc.** (inputs change by status).
- **Question budget:** **5** max. **Tone:** genuinely friendly/human. **Output:** downloadable form.
- **Interface:** web chat. **Deployment:** public live URL, free host.
- **Must actually work end-to-end** — not a happy-path mock.

## 1.4 Deliverables — *Brief L93–97*

- **Source code** repo · **deployed URL + one-command local-run** fallback · **half-page DECISIONS note** (→ `docs/DECISIONS.md`, derived from §2).

## 1.5 Rules & scope — *Brief L99–103*

- Keep it **simple** (prototype, not product; resist scope creep) · **fake/test data only — no real PII, no filings, no e-filing** · **not tax advice**, and don't pretend to be.

## 1.6 Judging priority (optimize in this order) — *Brief L81–91*

1. **Harness quality** (highest) → 2. **Actually works** → 3. **Conversation quality** → 4. **Soundness of decisions**.
**NOT judged:** visual/UI polish — keep the front end minimal.

## 1.7 Requirements traceability matrix (atomized — every brief item, cited)

**This is the completeness checklist.** Every normative item in the brief appears here exactly once
(duplicate statements merged, all sources cited). *If it isn't in this table, it isn't in the brief.*
**Owner** = the module/artifact responsible (→ §A); **Verified by** = how we prove it.

### Pillars *(Brief L17–29)*
| ID | Requirement | Source | Owner | Verified by |
|----|-------------|--------|-------|-------------|
| P1 | Chat loop carries state across turns | L23 | `agent/loop.py`, `web/session.py` | e2e: state persists across turns |
| P2 | Tools take real actions; ≥1 produces the filled return | L24 | `agent/tools.py` | tool call → PDF bytes |
| P3 | Guardrails: on-task/safe/bounded + input validation + limits | L25 | `agent/guardrails.py`, `core/models.py` | unit: bad input rejected; counter capped |
| P4 | Observation: actions & decisions visible | L26 | `obs/trace.py`, `/trace` + UI | trace shows tool calls/decisions |
| P5 | Pillars **enforced & visible** (code + running), not cosmetic | L19–21, L28 | all above | judge demo |

### Functional / Definition-of-Done + Fixed constraints *(L32–58)*
| ID | Requirement | Source | Owner | Verified by |
|----|-------------|--------|-------|-------------|
| F1 | Web-based chat interface | L36, L56 | `web/routes.py`, `web/static/` | open URL, chat works |
| F2 | Supply realistic fake W-2 (~$40k earner) the user provides | L37, L51 | `docs/w2_filled_sample_2025.pdf` ✅ | fixture exists, vision-readable |
| F3 | Agent reads/ingests the uploaded W-2 | L70 (impl. of L37/L40) | `agent/extractor.py` | round-trip vs sample W-2 pdf |
| F4 | **≤5 questions** asked | L38, L53 | `agent/loop.py` counter | unit: counter cannot exceed 5 |
| F5 | Warm, human conversation (judged) | L39, L54 | `agent/prompts.py` | review + e2e transcript |
| F6 | Fill **2025 Form 1040** from W-2 + answers | L40, L50 | `core/pdf_filler.py`, `form_map/` | golden test: fields correct |
| F7 | Support **filing-status** variation (single/MFJ/HoH…) | L52 | `core/tax_engine.py`, `config/` | unit per status |
| F8 | **Downloadable** completed form | L41, L55 | `web/routes.py` `/download` | e2e: valid PDF downloads |
| F9 | **Deployed** to public URL (Render/comparable free) | L42, L57 | `render.yaml` | live URL reachable |
| F10 | Works **end-to-end** (no happy-path mock) | L58 | full system | e2e happy path |

### Deliverables / Rules / Open decisions *(L93–103, L62–79)*
| ID | Requirement | Source | Owner | Verified by |
|----|-------------|--------|-------|-------------|
| V1 | Source code in a repo | L95 | repo | exists |
| V2 | Live URL + **one-command local run** fallback | L96 | `render.yaml`, `Makefile`/README | `make run` works |
| V3 | **DECISIONS note** (½ page, choices + why) | L97 | `docs/DECISIONS.md` ← §2 | exists, ≤1 page |
| S1 | Keep simple; resist scope creep | L101 | §A, §7 | review |
| S2 | Fake/test data only; no real PII/filings/e-file | L102 | `agent/guardrails.py`, fixtures | no real PII present |
| S3 | **Not tax advice**; must not pretend | L103 | `agent/guardrails.py` + disclaimer | unit: advice → refusal |
| O1 | All **open items chosen + justified** (lang, model, fill, read, tax, guardrails, convo, state, host, test) | L62–79 | §2 (+ `DECISIONS.md`) | §2 complete |

### Optional stretch *(L105–110 — not required to pass)*
| ID | Requirement | Source | Owner |
|----|-------------|--------|-------|
| T1 | 2nd filing status / a dependent handled gracefully | L107 | tax_engine, loop |
| T2 | Correct an answer mid-conversation | L108 | loop/state |
| T3 | Observation trail surfaced **in the UI** (not just logs) | L109 | `web/static/` panel |
| T4 | Validate W-2 + recover from messy/partial data | L110 | extractor + guardrails |

---

# PART 2 — DECISIONS, VERIFIED FACTS & SOFT / IMPLIED REQUIREMENTS

## 2. Committed decisions (the brief's open items — our calls + why) — *Brief L62–79*

Canonical decision record. `docs/DECISIONS.md` (the ½-page deliverable, V3) is the prose distillation
of this table — **keep them in sync; this table is the source of truth.**

| Open item | Decision | Why |
|-----------|----------|-----|
| Language & framework (L67) | **Python + FastAPI** | pypdf fills the provided 2025 1040 cleanly (verified, 229 fields); Anthropic SDK native PDF/vision; minimal Render surface. |
| LLM / model (L68) | **Claude Sonnet 4.6** default, **Opus 4.8** fallback | Strong vision + tool use at low latency/cost; Opus for the hardest reasoning. |
| Obtain & fill the 1040 (L69) | Provided fillable `docs/f1040.pdf` → **pypdf** AcroForm write → flatten → stream bytes | No sourcing; deterministic; verified fillable. |
| W-2 source & read (L70) | User **uploads**; **Claude vision → schema-validated `W2` object** (`extract_w2`) | Most agentic; handles real/messy forms; showcases Tools + Guardrails. |
| Tax computation (L71) | **Exact IRS Tax Table** (<$100k), constants in **year-keyed config**, **half-up** rounding | Matches a real return to the dollar; defensible accuracy. |
| Guardrail enforcement (L72) | **Code + schema** (Pydantic) + hard counter + scope refusals | "Enforced & visible" beats prompt-only. |
| Conversation design (L73) | ≤5 Qs; identity/wages come from the W-2 so Qs spend on status / dependent-of-another / other-income / itemize-confirm; warm, one at a time | Stays within budget; human tone. |
| State & sessions (L74) | **In-memory** session store keyed by id (W-2, answers, counter, lines, PDF) | Simple; sufficient for a prototype. |
| Hosting (L75) | **Render** free web service; API key as secret; ephemeral FS (stream PDF) | Free, easy, judge-reachable. |
| Testing (L76) | **Golden test** + extraction round-trip + e2e happy path | Proves "actually works" independent of LLM variance. |

## 3. Verified facts (locked — do not regress)

| Fact | Value | Why it matters |
|------|-------|----------------|
| Provided 1040 | `docs/f1040.pdf` **is the official 2025 Form 1040** (title "2025 Form 1040"), **fully fillable, 229 AcroForm fields** (`…f1_NN[0]` text, `c1_N[0]` checkboxes). | Fill the form we have — no sourcing. |
| **2025 standard deduction** | **Single $15,750 · MFJ $31,500 · HoH $23,625 · MFS $15,750** — OBBBA-adjusted (Jul 2025). | ⚠️ **#1 accuracy trap.** NOT the $15,000/$30,000 originally in Rev. Proc. 2024-40. |
| 2025 brackets (single) | 10% ≤ $11,925 · 12% ≤ $48,475 · 22% ≤ $103,350 · 24% ≤ $197,300 · … | Feed the Tax Table; unchanged by OBBBA. |
| Tax Table rule | Taxable income **< $100,000 ⇒ IRS Tax Table required** ($50-range midpoint, whole-dollar, half-up). | Our profile must use the table, not raw bracket math. |
| Empty 2025 W-2 | `https://www.irs.gov/pub/irs-prior/fw2--2025.pdf` (✅ `docs/w2_blank_2025.pdf`). | Live `fw2.pdf` is now **2026**; prior-year URL is the correct **2025**. |
| Sample W-2 (golden) | wages $48,000 → std 15,750 → **taxable 32,250** → **tax ≈ $3,635** → withheld 4,250 → **refund ≈ $615**. | Deterministic golden-test target; expected lines asserted in `tests/test_tax_engine.py`. |

## 4. Soft / implied requirements (what the hard reqs force us to build)

### 4.1 Components
FastAPI app · in-memory session store · `POST /chat` · `POST /upload` · Anthropic client · agent loop ·
tool registry · **W-2 extractor** · **tax engine** · **1040 filler** · `GET /download/{session}` ·
`GET /trace/{session}` · minimal HTML/JS front end. (Module homes in §A.)

### 4.2 Tools (the Tools pillar, concretely)
| Tool | Signature | Notes |
|------|-----------|-------|
| `extract_w2` | `(file_bytes) → W2` | Claude vision → fields validated against the `W2` schema. |
| `compute_1040` | `(W2, answers) → LineItems` | **Pure, deterministic, zero-LLM.** Wages → AGI → std deduction → tax (table) → withholding → refund/owe, across filing statuses. The heart of "actually works." |
| `fill_1040_pdf` | `(LineItems) → pdf_bytes` | pypdf writes AcroForm fields via `form_map/`; flatten; return bytes. |
| helpers | `standard_deduction(status, year)`, `tax_from_table(taxable, status, year)` | read `config/`; no magic numbers. |

### 4.3 Conversation design (the ≤5 questions)
W-2 supplies **name, SSN, address, wages, withholding** → those cost **zero** questions. Core budget:
1. **Filing status** *(F7)* — single / MFJ / HoH / …
2. **"Can someone else claim you as a dependent?"** — adjusts the standard deduction.
3. **"Any income besides this W-2 in 2025?"** — **scope gate**: if yes, gracefully flag out-of-scope (§7), don't silently mishandle.
4. **Standard-deduction confirm** — itemizing is out of scope; confirm standard.
- Warmth rules: acknowledge, explain *why* you ask, never dump a form, summarize before filing. Fewer than 5 is fine; the cap is hard.
- *Stretch:* claiming dependents → CTC/ODC (T1); mid-conversation correction (T2).

### 4.4 Tax engine
Std-deduction table (§3) → **Tax-Table lookup** (<$100k, $50 midpoint, whole-dollar, **half-up**) →
total tax → vs withholding → **refund or owed**. 1040 lines for our scope: **1a/1z** wages · **9**
total income · **11** AGI · **12** std deduction · **15** taxable · **16** tax · **22/24** total tax ·
**25a/25d** withholding · **33** payments · **34/35a** refund *or* **37** owed. (Credit lines = 0 in core scope.)

### 4.5 1040 field mapping
One-time discovery → persist as **`form_map/f1040_2025.py`** (SSOT: line → AcroForm field name). Dump
fields with pypdf; resolve via the `f1_NN` naming or a fill-with-own-name render. **Flagged gotcha**; budget ~10 min.

### 4.6 Guardrails (code + schema, not just prompt)
Pydantic `W2`/`Answers` validation (reject/repair) · numeric plausibility (wages ≥ 0, withholding ≤ wages,
box 3/5 ≈ box 1, SSN/EIN format) · **scope refusals** (no advice; decline >1 W-2, 1099, itemizing — *S3, §7*) ·
**hard ≤5 counter in code** · fake-data posture + persistent **"not tax advice"** disclaimer.

### 4.7 Observation
Per-turn structured trace: user input → model message → tool calls (name + args) → results → computed
lines → decision/next phase. To **logs** + a **`/trace` UI panel** (T3) so a judge sees the reasoning.

### 4.8 State & sessions
Session id; in-memory state = W-2 + answers + question count + computed lines + generated PDF; reset/new-session.

### 4.9 Deployment
Render web service · `ANTHROPIC_API_KEY` secret · `uvicorn … --port $PORT` · **ephemeral FS** (build
PDF in memory, stream it) · pinned `requirements.txt` · one-command local run (`make run`).

### 4.10 Testing / proof
- **Golden (no LLM):** `compute_1040(W2(wages=48000, withholding=4250), single)` → Line 15 = 32,250, Line 16 = 3,635, refund = 615. Input **and** expected lines are written in the test (hand-verified) — it proves correctness, not self-consistency.
- **Extraction round-trip:** `extract_w2(docs/w2_filled_sample_2025.pdf)` → the box values the test asserts (48000, 4250, …).
- **E2E happy path:** upload → ≤5 answers → correctly-filled, downloadable 1040.

---

# PART 3 — EXECUTION

## A. Architecture & file structure (SOLID · DRY · SSOT · no hard-coding)

**Design mandates (apply to all code):**
- **SSOT / no hard-coding.** No taxpayer/W-2 data in code; no scattered magic numbers. Two app
  single-sources: tax constants → `config/tax_year_2025.py`; 1040 field names → `form_map/f1040_2025.py`.
  (Sample-W-2 data lives only in its generator/tests, never in app code.) Secrets → env only.
- **Tax-year parameterized (Open/Closed).** No literal `2025` in logic; the year selects a config
  module. Adding 2026 = new `config/tax_year_2026.py` + `form_map/f1040_2026.py`, **zero** engine edits.
- **Deterministic spine isolated from the LLM (Dependency Inversion).** `core/` is pure, importable,
  unit-tested, with **no** Anthropic dependency. `agent/` orchestrates, depending on tool *interfaces* + `core`.
- **One responsibility per module (SRP);** thin `core/models.py` schemas are the contracts between layers (ISP).

```
agent-tax/
├── README.md                      # one-command run (V2)
├── requirements.txt               # pinned deps
├── Makefile                       # make run | make test | make fixtures
├── render.yaml                    # deploy SSOT (F9, V2)
├── .env.example                   # ANTHROPIC_API_KEY (never commit secrets)
├── config/
│   └── tax_year_2025.py           # SSOT: std deductions, brackets, tax-table params
├── form_map/
│   └── f1040_2025.py              # SSOT: 1040 line → AcroForm field name
├── src/agent_tax/
│   ├── main.py                    # FastAPI app (uvicorn target)
│   ├── core/                      # deterministic spine — NO LLM
│   │   ├── models.py              # Pydantic W2, Answers, LineItems (guardrail contracts; P3)
│   │   ├── tax_engine.py          # compute_1040(): deductions, tax, refund/owe (F6, F7)
│   │   ├── tax_tables.py          # tax_from_table() — reads config
│   │   └── pdf_filler.py          # fill_1040_pdf(): pypdf AcroForm write (F6)
│   ├── agent/                     # the harness
│   │   ├── loop.py                # chat loop, state machine, ≤5 counter (P1, F4)
│   │   ├── tools.py               # tool registry (P2)
│   │   ├── extractor.py           # extract_w2(): Claude vision → W2 (F3)
│   │   ├── guardrails.py          # validation, plausibility, scope refusals (P3, S2, S3)
│   │   └── prompts.py             # system prompt + conversation guidance (F5)
│   ├── obs/
│   │   └── trace.py               # structured observation (P4)
│   └── web/
│       ├── routes.py              # /chat /upload /download /trace (F1, F8)
│       ├── session.py             # in-memory session store (P1, F1)
│       └── static/                # minimal chat UI + trace panel (F1, T3)
├── scripts/
│   └── generate_sample_w2.py      # stamps values onto genuine IRS Copy B ✅
├── docs/                          # SPECS, brief, DECISIONS, fixtures
└── tests/
    ├── test_tax_engine.py         # golden (F6, F7)
    ├── test_pdf_filler.py         # fields land right (F6)
    └── test_extractor.py          # round-trip vs sample W-2 pdf (F3)
```
The **Owner** column in §1.7 maps each REQ-ID to a module here — requirement → component traceability.

## 5. One-hour agentic build plan (critical path + cut-lines)

| Time | Work | Why first / cut-line |
|------|------|----------------------|
| **0–10** | Scaffold + `config/` + `form_map/` discovery + `core/tax_engine` (pure fn) | Deterministic core is highest-risk-to-"it works" — and needs **no** LLM. |
| **10–25** | `core/pdf_filler` + **golden test green** | Provably-correct filler exists before any agent. **Hard floor of the demo.** |
| **25–40** | `agent/` loop + tools + W-2 vision extraction | The harness/pillars, orchestrating the tested core. |
| **40–50** | `web/` chat UI + upload + `/download` + session | Usable end-to-end. |
| **50–60** | **Deploy to Render** + live smoke test with the sample W-2 | Live URL is a hard deliverable; leave slack for cold-start/env. |
| *If time* | Trace UI panel (T3) · MFJ (T1) · correction (T2) · messy-W-2 recovery (T4) | Stretch — only after the core is solid. |

**Agentic principle:** build & unit-test the **deterministic spine** (`core/`) *before* wiring any
model, so "does it actually work" is guaranteed independent of LLM variance; the agent is reduced to
*orchestration over trusted tools*.

## 6. Risks / gotchas (miss nothing)
- ⚠️ **OBBBA standard deduction** — $15,750 single, not $15,000.
- **Tax Table vs bracket math** — reproduce the table for <$100k; round **half-up** ($3,634.50 → $3,635). Python's `round()` is *banker's* → $3,634 (wrong). Cross-check the published 2025 table.
- **AcroForm field-name discovery** — fiddly; persist to `form_map/`.
- **Render cold start + ephemeral FS** — stream PDF from memory; expect a slow first request.
- **API-key secrecy** — env var only; never in the repo.
- **Vision extraction reliability** — handle rotated/blurry/partial; validate + re-ask.
- **5-question budget vs. data needed** — defaults so the cap is never the blocker.
- **Download headers** — `Content-Type: application/pdf` + `Content-Disposition`.
- **Not-tax-advice framing** — visible disclaimer; refuse advice gracefully.

## 7. Out of scope (resist scope creep — *S1*)
E-filing · real PII · **more than one W-2** · **non-W-2 income** (1099, interest, self-employment) ·
**itemized deductions** · **tax credits** (CTC/ODC/EITC…) · **state/local returns**. The app handles
**any single W-2** across filing statuses with the standard deduction; out-of-scope inputs are
**detected and gracefully declined** with a clear message — never silently mishandled. Scope extends
by **adding a module** (Open/Closed), not rewriting.

## 8. Assumptions (defaults when unasked)
- **Scope = any single straightforward W-2.** Nothing is tied to the sample taxpayer; the same flow works for any uploaded W-2.
- Sample earner ~**$48,000** (user's call; brief says ~$40k — both a single modest-income W-2 earner).
- Skip-defaults: **single**, **not a dependent**, **no other income**, **standard deduction**, refund shown on screen.
- 2025 figures per OBBBA + Rev. Proc. 2024-40 (§3).

## 9. Artifact inventory — real / reference / test / throwaway

Labeled so it's clear what ships, what's a fixture, and what to delete.

- **REAL (ships, read at runtime):** `docs/f1040.pdf` — official 2025 1040 we fill (→ `assets/` at scaffold); all `src/`, `config/`, `form_map/` (to write).
- **REFERENCE (permanent, not shipped, not read at runtime):** `docs/w2_blank_2025.pdf` — genuine IRS 2025 W-2; the template the sample is stamped onto + source of the field map. Plus the brief, `SPECS.md`, `DECISIONS.md`.
- **TEST/DEMO FIXTURE (only tests + manual upload; never imported by app code):** `docs/w2_filled_sample_2025.pdf` — the fake W-2 a tester/judge uploads, and the extraction/e2e input (→ `tests/fixtures/` at scaffold). `scripts/generate_sample_w2.py` — dev tool that regenerates it by stamping values onto the genuine Copy B; not shipped (needs `reportlab` + `pypdf`).
- **THROWAWAY (delete when done):** `/tmp/w2gen` (venv) and `/tmp/*.png|pdf` (render checks) — outside the repo.
- **DELETED:** `docs/w2_filled_sample_2025.json` — it read like a runtime shortcut. Expected tax values now live in `tests/test_tax_engine.py`; the fixture's data lives in its generator. **No fixture is ever read by the app at runtime — it extracts from the uploaded W-2 and computes from tax law.**

**Sample-W-2 fidelity:** stamped onto the genuine IRS Copy B, so it looks exactly like a real form. Its OMB renders as "1545-0029" in non-Adobe viewers — a font quirk in the IRS's *own* file (identical in `w2_blank_2025.pdf` and the live IRS form); the true W-2 OMB is 1545-0008. No form text was altered.
