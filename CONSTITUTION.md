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

Data flow for FAQ content: `model/faq_rrhh.json` (source of truth, `ruta`/`area`
per entry) → `catalogo.py` generates `dist/faq.js` (static consumer) and feeds
`RRHHBot` directly (semantic and channel consumers). All three consumers read
the same file; don't let them drift into separate copies of the same facts.

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
  `whatsapp_service.py`'s `buscar_persona_por_telefono()` matches the
  sender's WhatsApp number against `empleados_mock.json`'s fictitious
  `telefono` field to return a personalized basic value (e.g. vacation
  balance) — anyone texting from that number sees that data, with no further
  proof of identity. This is deliberate and demo-appropriate (same spirit as
  caller ID), but it is not a trust boundary: never extend it to anything
  sensitive (salary, documents, changing data) without real verification
  (MFA or equivalent) first, and never describe it to a user as secure. If
  that verification is added later, it belongs in its own explicit step —
  don't silently upgrade this lookup's trust level in place.

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
