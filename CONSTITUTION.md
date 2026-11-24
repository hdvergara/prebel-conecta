# Prebel Conecta — Constitution

This document is the contract for anyone (human or agent) changing this project.
It has three parts: the **spec** (what this project is and must keep being true),
the **railguards** (hard rules that must never be violated), and the **harness**
(how work is verified before it's considered done).

Anything in `specs/plan.md` or a PR description that conflicts with this file is
wrong and must be fixed to match this file, not the other way around.

## 1. Spec

Prebel Conecta is a **demo HR portal** with two independent layers:

1. **Static layer** (`dist/`) — a zero-build HTML/CSS/JS site. It is published to
   GitHub Pages and MUST be fully usable with no backend running: profile switch,
   vacation request flow, payroll/certificate mock flows, keyword-based search
   (`suggestions()`), and the static FAQ list (from `dist/faq.js`) all work from
   static data alone (`dist/catalogo.js`, `dist/faq.js`).
2. **Semantic layer** (`model/`) — an optional, local-only Flask API
   (`model/rrhh_api.py`) wrapping `RRHHBot` (`model/rrhh_bot.py`): sentence
   embeddings for FAQ matching (`confianza`) + a pretrained sentiment classifier
   (`sentimiento`). The static layer calls it opportunistically
   (`MODEL_API` fetch with a short timeout) and degrades to the static fallback
   message when it isn't reachable. The semantic layer must never become a hard
   dependency of the static layer.

3. **Channel layer** (`model/whatsapp_service.py`) — an optional, local-only
   second consumer of `RRHHBot`, independent of `rrhh_api.py`: a webhook
   bridge to any WhatsApp Cloud API-compatible environment (the local emulator
   in the sibling `whatsapp-emulator/` folder today — not part of this repo,
   only a dev/test aid — or real Meta infrastructure later). It never runs in
   CI or in the static deploy; it's a developer-run process for manual testing.

4. **Agentic layer** (`n8n/`) — a separate system, run by the team on their
   own remote server (n8n + Ollama), outside this repo's CI and outside R1's
   fictional-data scope: it answers by retrieving snippets from the **real**
   Prebel documents (kept local-only, same as `.specs/`) and has a local LLM
   (Ollama) **write** the answer from them, rather than choosing a pre-written
   `faq_rrhh.json` entry. It never runs on the operator's machine and is not
   covered by this repo's test harness (§3) — see `n8n/README.md`.

Data flow for FAQ content: `model/faq_rrhh.json` (source of truth, `ruta`/`area`
per entry) → `catalogo.py` generates `dist/faq.js` (static consumer) and feeds
`RRHHBot` directly (semantic and channel consumers). All three consumers read
the same file; don't let them drift into separate copies of the same facts.

### The three-tier chain (Predictive → ML → Agentic)

Every entry point — the portal, WhatsApp, and the n8n chat bubble — answers
through the same escalating order, cheapest/fastest first, each tier only
reached when the one before it couldn't confidently answer:

| Tier | What | Where |
|---|---|---|
| 0 — Predictive | Keyword match, instant, free | `dist/app.js`'s `rank()` (web); the Cerebro's greeting/menu detector (n8n) |
| 1 — ML | Chosen pre-written FAQ answer, `model/rrhh_bot.py`, <1s, free | `model/rrhh_api.py`'s `/reply`, called directly by the web portal and by n8n's Cerebro (`n8n/workflows/03-cerebro-ia.json`) as its own first step |
| 2 — Agentic | LLM-composed answer from real documents, ~20s | n8n's Cerebro RAG+Ollama step, reached by WhatsApp and by the portal's gated chat bubble ("Puerta Web") |

This is why `model/rrhh_api.py` also ships containerized (see `Dockerfile`):
Tier 1 must be reachable from wherever Tier 2 runs, not just from
`127.0.0.1`.

## 2. Railguards

These are non-negotiable. A change that violates one of these is a bug, not a
style preference.

- **R1 — Public repo discipline.** `hdvergara/prebel-conecta` is a **public**
  GitHub repo. Never commit real personal data: no real employee names, phone
  numbers, personal/corporate emails, salaries, or policy figures from internal
  Prebel documents. `specs/` (real HR source documents) is gitignored and stays
  that way — never remove it from `.gitignore`, never copy its raw contact
  details into a file that gets committed (`model/faq_rrhh.json` included).
  Before any commit that touches `model/` or adds new content, grep the diff for
  phone-number patterns, `@prebel.com.co` style emails, and real full names.
- **R2 — Static-first.** Nothing in `dist/` may require the Flask API to
  render or to complete its core flows. Any new feature that calls `MODEL_API`
  must have a working fallback path that does not depend on the fetch
  succeeding, and must not block the UI waiting on it beyond the existing
  short timeout.
- **R3 — No secrets in client code.** `dist/*.js` ships to every visitor's
  browser. Never put API keys, tokens, or non-public URLs in it. `MODEL_API`
  pointing at `127.0.0.1` is fine because it only ever resolves on the
  operator's own machine.
- **R4 — Demo data stays fictitious.** `catalogo.py`'s `personas`/`areas` data
  (dist side) is fictitious by design ("Datos ficticios" in the footer) and
  must stay that way. Do not replace it with real employee data, even for a
  "better demo."
- **R5 — Fictitious bracket placeholders ([X], [sistema], [portal]…) in
  `faq_rrhh.json` are intentional template markers**, not bugs — don't silently
  invent concrete values for them. If real values become available, source them
  from `specs/` (local-only) and keep R1 in mind for anything derived from it.
- **R6 — Channel secrets stay out of the repo.** `model/whatsapp_service.py`'s
  connection parameters and secrets (`WA_ACCESS_TOKEN`, `WA_VERIFY_TOKEN`,
  `WA_APP_SECRET`, …) are read from environment variables / `.env` only —
  never hardcoded, never committed. `.env.example` holds placeholder values
  that only work against a freshly started local emulator; `.env` itself is
  gitignored at the repo root (not `prebel-conecta/.env` — this file *is* the
  repo root, so that path never matched). If `.gitignore` is ever edited,
  re-verify with `git check-ignore -v .env` that it's still excluded.
- **R7 — WhatsApp sender identification is basic, not authentication.**
  `whatsapp_service.py` has two identification paths, both equally informal:
  `buscar_persona_por_telefono()` matches the sender's WhatsApp number
  against `empleados_mock.json`'s fictitious `telefono` field (same spirit as
  caller ID), and `buscar_persona_por_documento()` accepts whatever
  `numero_documento` the sender types in chat (`IDENTIFICADOS_POR_DOCUMENTO`,
  an in-memory, per-process cache — lost on restart, not shared across
  processes) — self-reported, with no corroboration at all, weaker than the
  phone match. Either way, anyone claiming that number or typing that
  document number sees that data, with no further proof of identity. This is
  deliberate and demo-appropriate, but neither is a trust boundary: never
  extend either to anything sensitive (salary, documents, changing data)
  without real verification (MFA or equivalent) first, and never describe
  either to a user as secure. If that verification is added later, it
  belongs in its own explicit step — don't silently upgrade either lookup's
  trust level in place.
- **R8 — The tier chain's order and fallthrough must be preserved.** Any
  change touching the three-tier chain above (adding a tier, changing what
  triggers escalation) must keep cheaper/faster tiers tried before
  slower/heavier ones, and every escalation must be a graceful fallthrough,
  never a hard dependency: Tier 1's HTTP call from the Cerebro uses
  `onError: continueErrorOutput` specifically so an unreachable Tier 1 falls
  through to Tier 2 instead of breaking the whole answer — same spirit as
  R2, now applied across systems, not just within `dist/`.

## 3. Harness

"Done" means green on both suites below, not just "I read the code and it
looks right."

### Unit tests (pytest) — fast, no network, no real ML models

- Location: `prebel-conecta/tests/`.
- `RRHHBot` and the sentiment pipeline are **mocked** in unit tests
  (`SentenceTransformer`/`pipeline` are patched before `RRHHBot()` is
  constructed). Unit tests must run in well under a second each and must not
  download or load the real ~1GB of model weights. If a test needs the real
  model, it is not a unit test — it belongs in a manual/integration check, not
  in this suite.
- Run: `pytest prebel-conecta/tests -v` from the repo root (with `.venv`
  active, `pip install -r prebel-conecta/requirements-dev.txt`).

### JS unit tests (Node's built-in `node:test`) — pure logic only

- Location: `prebel-conecta/tests/js/`.
- Only for pure helper functions extracted from `dist/app.js` logic
  (`ownerLabel`, `rank`, `normalizeCatalog`, `weekdays`) via the same
  vm-context load pattern used during development. No network, no browser.
- Run: `node --test prebel-conecta/tests/js`.

### E2E tests (Playwright) — real browser, mocked network boundary

- Location: `prebel-conecta/e2e/`.
- Tests drive the real static site in a real browser against the behavior
  that must stay stable for every visitor. They do **not** depend on a real
  Flask backend being installed or running: any call to `MODEL_API` is
  intercepted with `page.route()` and given a fixed, deterministic JSON
  response. This is the core of the **green test strategy** — e2e tests must
  pass identically on a machine that has never installed `sentence-transformers`
  or downloaded any model, and must never be flaky because a real model's
  score shifted by a few hundredths.
  Why this is safe: the Flask contract (`/reply` → `{reply, ruta, area,
  confianza, sentimiento}`) is independently covered by the pytest suite above,
  so e2e doesn't need to re-verify the model's own correctness — only that the
  frontend wires that contract into the UI correctly.
- Every spec file documents each test with a **Context / Given / When / Then**
  comment block directly above the test body (see
  `prebel-conecta/e2e/tests/search.spec.js` for the pattern). Context is the
  page/state the test starts from; Given is the precondition; When is the
  user action; Then is the observable outcome the assertion checks.
- Run: `cd prebel-conecta/e2e && npx playwright install --with-deps chromium`
  once, then `npx playwright test`.

### Before calling anything done

1. `pytest prebel-conecta/tests -v` — green.
2. `node --test prebel-conecta/tests/js` — green.
3. `npx playwright test` (from `prebel-conecta/e2e/`) — green.
4. Re-read R1 against the actual diff if `model/` or anything derived from
   `specs/` changed.
