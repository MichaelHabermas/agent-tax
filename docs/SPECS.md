# SPECS — Agentic Tax-Filing Assistant (2025 Form 1040)

> Spec sheet for the hackathon build. **Part 1** is the *hard* requirements (non-negotiable, lifted
> from the brief). **Part 2** is the *soft / implied* requirements — what those hard requirements
> actually force us to build. **Part 3** is the agentic ~1-hour build plan, risks, scope, and
> assumptions. Source brief: `docs/Hackathon Challenge — Build an Agentic Tax-Filing Assistant.md`.

---

## 0. TL;DR

Build a **web chat** where a person uploads a single W-2 (~$40–50k earner), answers **≤5 friendly
questions**, and downloads a **completed 2025 IRS Form 1040**. The system must visibly demonstrate
four harness pillars — **chat loop, tools, guardrails, observation** — and be **deployed to a public
URL** (Render or comparable free host). Judged first on *harness quality*, then *does it actually
work end-to-end*, then *conversation quality*, then *soundness of our open-item decisions*. UI polish
is explicitly **not** judged.

**Locked decisions (see §2):** Python + FastAPI · Claude (Sonnet 4.6 default, Opus 4.8 fallback) ·
W-2 read by **Claude vision → schema-validated JSON** · 1040 filled with **pypdf** on the provided
`docs/f1040.pdf` · tax computed via the **exact IRS Tax Table** · guardrails in **code + schema** ·
deploy to **Render**.

---

# PART 1 — HARD REQUIREMENTS (non-negotiable)

## 1.1 The Four Pillars (required — the highest-weighted judging axis)

A judge must be able to point at code **and** the running system and see each pillar working.
"It's in the prompt" is explicitly weaker than "it's enforced and visible."

| # | Pillar | The bar | Our concrete realization (see §4) |
|---|--------|---------|-----------------------------------|
| 1 | **Chat loop** | Conversational loop that **carries state across turns**. | Session-scoped state machine; each turn appends to history and advances a phase. |
| 2 | **Tools** | Agent takes **real actions** through defined tools — at minimum, something that **produces the filled return**. | `extract_w2`, `compute_1040`, `fill_1040_pdf` as schema-typed tools the model invokes. |
| 3 | **Guardrails** | Constraints that keep it **on-task, safe, bounded**: what it will/won't do, **validation of inputs**, **limits it respects**. | Pydantic schema validation, numeric plausibility checks, scope refusals, hard ≤5-question counter in code. |
| 4 | **Observation** | Its behavior is **observable**: you can see what it did, the decisions it made, the actions it took. | Structured per-turn trace (inputs → tool calls + args + results → computed lines → decision), to logs + UI panel. |

## 1.2 Definition of Done (end-result checklist)

- [ ] **Web-based chat** a user can interact with.
- [ ] User provides a **W-2 for a ~$40k earner** — we supply a realistic fake one (✅ `docs/w2_filled_sample_2025.pdf`).
- [ ] Agent asks **no more than 5 questions**.
- [ ] Conversation feels **warm and human** — friendly, clear, not robotic/interrogative. *(Explicitly part of the bar.)*
- [ ] Agent fills a **2025 IRS Form 1040** from the W-2 + answers.
- [ ] Completed 1040 is **downloadable as a file** when finished.
- [ ] System is **deployed to a public URL** on **Render or comparable free, easy host** — reachable by a judge.

## 1.3 Fixed constraints (do not change)

- **Form:** U.S. Federal **Form 1040**, **tax year 2025**.
- **Taxpayer:** single W-2, **~$40k/year** (we use ~$48k — see §8).
- **Filing status:** must handle **single, married-filing-jointly, etc.** (inputs change by status).
- **Question budget:** **5 questions** max, asked of the user.
- **Tone:** genuinely friendly, human-quality.
- **Output:** a **downloadable completed form**.
- **Interface:** a **web chat**.
- **Deployment:** publicly reachable live URL on a free/easy host.
- **Must actually work end-to-end** — not a happy-path mock of one step.

## 1.4 Deliverables

- **Source code** in a repository.
- **Deployed running system** at a public URL **+ one-command local-run instructions as a fallback** (not a substitute).
- **Short DECISIONS note** (~half a page): the key open-item choices and *why*.

## 1.5 Rules & scope

- Keep it **simple** — a prototype, not a product. Resist scope creep; breadth ≠ goal.
- **Fake W-2 and test data only.** No real PII, no real filings, **no e-filing**.
- **Not tax advice** — and the agent **must not pretend** to give it.

## 1.6 Judging priority (optimize in this order)

1. **Harness quality** (highest weight) — are the four pillars real/enforced, or cosmetic?
2. **Does it actually work** — real W-2 in → real downloadable 1040 out, via chat, end-to-end.
3. **Conversation quality** — helpful-human feel within the 5-question budget.
4. **Soundness of decisions** — the open-item choices and how well we defend them.
5. **NOT judged:** visual/UI polish. Keep the front end minimal; spend effort on harness + working.

---

# PART 2 — VERIFIED FACTS + SOFT / IMPLIED REQUIREMENTS

## 3. Verified facts (locked — do not regress)

| Fact | Value | Why it matters |
|------|-------|----------------|
| Provided 1040 | `docs/f1040.pdf` **is the official 2025 Form 1040** (PDF title "2025 Form 1040"), **fully fillable, 229 AcroForm fields** (`topmostSubform[0].Page1[0].f1_NN[0]` text, `c1_N[0]` checkboxes). | No need to source a form — **fill the one we have** with pypdf. |
| **2025 standard deduction** | **Single $15,750 · MFJ $31,500 · HoH $23,625 · MFS $15,750** — OBBBA-adjusted (One Big Beautiful Bill Act, Jul 2025). | ⚠️ **#1 accuracy trap.** NOT the widely-cited $15,000/$30,000 from the original Rev. Proc. 2024-40. |
| 2025 brackets (single) | 10% ≤ $11,925 · 12% ≤ $48,475 · 22% ≤ $103,350 · 24% ≤ $197,300 · … | Bracket math feeds the Tax Table; thresholds unchanged by OBBBA. |
| Tax Table rule | For **taxable income < $100,000** the IRS **requires the Tax Table** ($50-range, midpoint, whole-dollar). | Our profile (~$32k taxable) **must** use the table, not raw bracket math, to match a real return. |
| Empty 2025 W-2 | `https://www.irs.gov/pub/irs-prior/fw2--2025.pdf` (✅ saved as `docs/w2_blank_2025.pdf`). | The live `fw2.pdf` is now the **2026** form; the prior-year URL is the correct **2025** one. |
| Sample W-2 (golden) | wages $48,000 → AGI 48,000 − std 15,750 = **taxable 32,250** → **tax ≈ $3,635** → withheld 4,250 → **refund ≈ $615**. | Deterministic target for the golden test. Mirrors `docs/w2_filled_sample_2025.{pdf,json}`. |
| Tooling | `python3`, `pypdf 6.9.2`, `node v22` present; `reportlab` installed for fixture gen. | Stack is viable locally today. |

## 4. Soft / implied requirements (what the hard reqs force us to build)

### 4.1 Components

FastAPI app · session store (in-memory dict keyed by session id) · `POST /chat` · `POST /upload`
(W-2) · Anthropic client · agent loop · tool registry · **W-2 extractor** · **tax engine** ·
**1040 filler** · `GET /download/{session}` · observation/trace recorder · minimal HTML/JS front end.

### 4.2 Tools (the Tools pillar, concretely)

| Tool | Signature | Notes |
|------|-----------|-------|
| `extract_w2` | `(file_bytes) → W2` | Claude vision reads the upload → JSON validated against the `W2` schema. |
| `compute_1040` | `(W2, answers) → LineItems` | Pure function. Deterministic. The heart of "actually works." Unit-testable with **zero** LLM. |
| `fill_1040_pdf` | `(LineItems) → pdf_bytes` | pypdf writes AcroForm fields on `f1040.pdf`; flatten; return bytes. |
| (helpers) | schema validators, `standard_deduction(status)`, `tax_from_table(taxable, status)` | |

### 4.3 Conversation design (the ≤5 questions)

The W-2 already supplies **name, SSN, address, wages, withholding** → those cost **zero** questions.
Spend the budget on what the W-2 *can't* tell us. Canonical order (warm phrasing, one at a time):

1. **Filing status** — single / married filing jointly / head of household / …
2. **"Can someone else claim you as a dependent?"** (e.g., a parent) — changes the standard deduction.
3. **Dependents you're claiming** — drives CTC/ODC and head-of-household eligibility.
4. **Any income besides this W-2 in 2025?** — interest, a second job, freelance (keeps us honest about AGI/scope).
5. **Standard vs. itemize confirm** — "I'll use the standard deduction unless you had big deductible expenses — sound right?"

- Questions 2–5 are **skippable** when the W-2 + safe defaults already determine the answer (fewer is fine; the cap is 5).
- Warmth rules: acknowledge what they said, explain *why* you're asking, never dump a form, summarize before filing.
- **Mid-conversation correction** (stretch): let the user revise a prior answer; recompute downstream lines.

### 4.4 Tax engine

Standard-deduction table (§3) → **Tax Table lookup** for taxable income < $100k ($50-range midpoint,
whole dollar) → total tax → compare to withholding → **refund or amount owed**. 1040 lines touched
for our profile: **1a/1z** wages · **9** total income · **11** AGI · **12** std deduction · **15**
taxable income · **16** tax · **22/24** total tax · **25a/25d** withholding · **33** total payments ·
**34/35a** refund *or* **37** amount owed.

### 4.5 1040 field mapping

One-time discovery pass mapping computed values → AcroForm field names among the 229. Approach:
dump all field names with `pypdf`, then either (a) use the known `f1_NN` IRS naming, or (b)
fill-each-field-with-its-own-name, render, and read which box it lands in. **Flagged gotcha** — budget
~10 min; persist the mapping as a constant so it never has to be re-derived.

### 4.6 Guardrails (code + schema, not just prompt)

- **Schema validation:** Pydantic models for `W2` and `Answers`; reject/repair malformed extraction.
- **Numeric plausibility:** wages ≥ 0, withholding ≤ wages, box 3/5 ≈ box 1 sanity, SSN/EIN format.
- **Scope refusals:** no tax *advice*; decline unsupported income types / forms; stay on the 1040 task.
- **Hard question counter** enforced **in code** (not the prompt) — the loop physically cannot exceed 5.
- **PII / fake-data posture:** treat all input as test data; persistent **"not tax advice"** disclaimer.

### 4.7 Observation

Structured per-turn trace: user input → model message → tool calls (name + args) → tool results →
computed line items → decision/next phase. Emit to **logs** and (stretch) a **UI trace panel** so a
judge sees the reasoning, not just the chat.

### 4.8 State & sessions

Session id (cookie or generated); in-memory state holds the W-2, answers so far, question count,
computed lines, and the generated PDF. Support reset/new-session.

### 4.9 Deployment

Render web service · `ANTHROPIC_API_KEY` as a secret env var · start `uvicorn app:app --host 0.0.0.0
--port $PORT` · **ephemeral FS**: generate the PDF in memory and stream it (don't rely on disk
persistence) · `requirements.txt` pinned · one-command local run (`uvicorn …` or a `Makefile`/Docker).

### 4.10 Testing / proof

- **Golden test (no LLM):** `compute_1040(sample W2, single)` → Line 15 = 32,250, Line 16 = 3,635,
  refund = 615 (from `docs/w2_filled_sample_2025.json`).
- **Extraction round-trip:** `extract_w2(w2_filled_sample_2025.pdf)` → matches the JSON twin.
- **End-to-end happy path:** upload → 5 (or fewer) answers → downloadable, correctly-filled 1040.

---

# PART 3 — EXECUTION

## 5. One-hour agentic build plan (critical path + cut-lines)

| Time | Work | Why first / cut-line |
|------|------|----------------------|
| **0–10** | Scaffold FastAPI + **f1040 field-map discovery** + `tax_engine` as a pure function. | Deterministic core is the highest-risk-to-"it works" path — and needs **no** LLM. |
| **10–25** | `fill_1040_pdf` + **golden test green**. | Provably-correct filler exists even if the agent later misbehaves. **Hard floor of the demo.** |
| **25–40** | Agent loop + tool registry + **W-2 vision extraction**. | The harness/pillars. Tools call the already-tested core. |
| **40–50** | Minimal chat FE + upload + `/download` + session wiring. | Make it usable end-to-end. |
| **50–60** | **Deploy to Render** + live smoke test with the sample W-2. | A live URL is a hard deliverable; leave time for cold-start/env gotchas. |
| *If time* | Observation UI panel · MFJ path · answer-correction · messy-W-2 recovery. | Stretch goals — only after the core is solid. |

**Agentic principle:** build and unit-test the **deterministic spine** (tax + fill) *before* wiring
any model, so "does it actually work" is guaranteed independent of LLM variance, and the agent is
reduced to *orchestration over trusted tools*.

## 6. Risks / gotchas (miss nothing)

- ⚠️ **OBBBA standard deduction** — use $15,750 single, not $15,000.
- **Tax Table vs bracket math** — must reproduce the table for < $100k. Round half **up** (IRS convention): the $48k profile is $3,634.50 → **$3,635**; Python's `round()` uses *banker's* rounding → $3,634 (wrong). Cross-check the published 2025 Tax Table.
- **AcroForm field-name discovery** — fiddly; persist the mapping.
- **Render cold start + ephemeral FS** — stream PDF from memory; expect a slow first request.
- **API-key secrecy** — env var only; never in the repo.
- **Vision extraction reliability** — handle rotated/blurry/partial W-2s; validate + re-ask, don't trust blindly.
- **5-question budget vs. data needed** — design defaults so the cap is never the blocker.
- **Download headers** — correct `Content-Type: application/pdf` + `Content-Disposition` filename.
- **Not-tax-advice framing** — visible disclaimer; refuse advice gracefully.

## 7. Out of scope (resist scope creep)

E-filing · real PII · income beyond one W-2 (1099 = stretch) · itemized deductions · credits beyond
standard + CTC/ODC · state returns · multi-W-2 aggregation (unless trivially added).

## 8. Assumptions (defaults when unasked)

- Sample earner is **~$48,000** (user's call; brief says ~$40k — both are a single modest-income W-2 earner; documented, not a miss).
- Defaults if a question is skipped: **single**, **not a dependent**, **no dependents**, **W-2-only income**, **standard deduction**, refund shown on screen.
- 2025 figures per OBBBA + Rev. Proc. 2024-40 (§3).

## 9. Fixtures produced for this build

- `docs/f1040.pdf` — official **2025** Form 1040, fillable (provided).
- `docs/w2_blank_2025.pdf` — official **2025** blank W-2 (IRS prior-year).
- `docs/w2_filled_sample_2025.pdf` — realistic filled W-2 (Jordan A. Rivera, ~$48k, SSN 111-11-1111).
- `docs/w2_filled_sample_2025.json` — golden-test twin of the sample W-2 + expected 1040 lines.
