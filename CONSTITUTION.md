# Prebel Conecta — Constitution

This document is the contract for anyone (human or agent) changing this project.
It has three parts: the **spec** (what this project is and must keep being true),
the **railguards** (hard rules that must never be violated), and the **harness**
(how work is verified before it's considered done).

Anything in `specs/plan.md` or a PR description that conflicts with this file is
wrong and must be fixed to match this file, not the other way around.

## 1. Spec

Prebel Conecta is a **demo HR portal** with four independent layers:

1. **Static layer** (`dist/`) — a zero-build HTML/CSS/JS site. It is published to
   GitHub Pages and MUST be fully usable with no backend running: profile switch,
   vacation request flow, payroll/certificate mock flows, keyword-based search
   (`suggestions()`), and the static FAQ list (from `dist/faq.js`) all work from
   static data alone (`dist/catalogo.js`, `dist/faq.js`).
2. **Semantic layer** (`model/`) — an optional, local-only Flask API
   (`model/rrhh_api.py`) wrapping `RRHHBot` (`model/rrhh_bot.py`): sentence
   embeddings for FAQ matching (`confianza`, `tipo`) + a pretrained sentiment
   classifier (`sentimiento`). `model/orquestador.py` is the engine that
   decides, for every call to `/reply`, whether that match is confident
   enough to answer on its own or whether to escalate to the LLM connector
   (`model/conectores.py`) — see "The three-tier chain" below; Python, not
   n8n, orchestrates this. The static layer calls `/reply` opportunistically
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
   covered by this repo's test harness (§3) — see `n8n/README.md`. It serves
   two independent roles, unrelated to each other: (a) its own WhatsApp
   puertas (`01-puerta-emulador.json`, `02-puerta-evolution.json`) call it
   directly, exactly as before this section's pivot — unaffected by it; and
   (b) it is one possible **secondary** backend behind the LLM connector
   below (reachable over MCP), used only when the team points
   `model/conectores.py` at it instead of a local or commercial alternative.

Data flow for FAQ content: `model/faq_rrhh.json` (source of truth, `ruta`/`area`
per entry) → `catalogo.py` generates `dist/faq.js` (static consumer) and feeds
`RRHHBot` directly (semantic and channel consumers). All three consumers read
the same file; don't let them drift into separate copies of the same facts.

### The three-tier chain (Predictive → ML → Agentic)

`model/orquestador.py` decides this for every call to `/reply` — Python
orchestrates the chain, not n8n. The thresholds below are editable data
(`model/arquitectura.json`), not hardcoded constants:

| Tier | Trigger | What happens |
|---|---|---|
| Predictive | `confianza` (from `RRHHBot.match()`) > `umbral_predictivo` (0.95) | The ML match is trusted as-is, no further step |
| ML | `umbral_llm` (0.75) ≤ `confianza` ≤ `umbral_predictivo` | The local semantic answer is returned as-is |
| Agentic (LLM) | `confianza` < `umbral_llm`, **or** the caller asks to continue (`seguir: true` in `/reply`'s body) | First checks `model/rag_retroalimentacion.py` for a question similar enough to one already answered before (`umbral_retroalimentacion`, 0.85) — if found, reuses that answer (`capa: "retroalimentacion"`, `tipo: "reusado"`) without calling the connector again; otherwise escalates to the active LLM connector (`model/conectores.py`), falling back to the ML answer already computed if it doesn't respond |

When the LLM connector answers a question the earlier tiers didn't have
with confidence, that question/answer is queued for manual review
(`model/retroalimentacion.py`) — never auto-promoted into `faq_rrhh.json`
(R1/R4 still apply to anything that might end up there). The reuse check
above is what later *consumes* that queue automatically; it is not a
fourth tier in this ratified chain, just an optimization inside the
escalation step so the same question doesn't pay the LLM's cost twice.

n8n's Cerebro remains reachable two ways, independent of each other: its own
WhatsApp puertas call it directly (unaffected by this chain), and it can
also serve as the LLM connector's backend over MCP (see layer 4 above) —
in that second role it's what Tier "Agentic" above escalates to, when
configured. `model/rrhh_api.py` also ships containerized (see `Dockerfile`
and `docker-compose.yml`, the deployable monolith) so it's reachable from
wherever a connector backend runs, not just from `127.0.0.1`.

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
  never a hard dependency: `model/orquestador.py` falls back to the ML
  answer already computed whenever the LLM connector returns `None`
  (unconfigured, unreachable, or no answer), same as the Cerebro's own
  `onError: continueErrorOutput` on its WhatsApp-side HTTP calls — same
  spirit as R2, now applied across systems, not just within `dist/`. The
  two thresholds live in `model/arquitectura.json`; changing them is editing
  that data, not this file or the orchestrator's code.
- **R9 — Layer separation.** The three tiers live in separate modules that
  never import "downward": `model/rrhh_bot.py` (ML) must never import
  `model/conectores.py`, `model/orquestador.py`, or
  `model/rag_retroalimentacion.py` (enforced by `tests/test_arquitectura.py`,
  not just documented here). The LLM tier is only ever reached through
  `model/conectores.py`'s `ConectorLLM` interface — no other module calls a
  specific backend (MCP, n8n, a commercial API) by name.
  `model/rag_retroalimentacion.py` never imports `rrhh_bot` either — it
  receives the embedding model by injection (`self.bot.model`, passed by
  `model/orquestador.py`), the only module allowed to import it. Swapping
  backends means changing what the connector points to,
  never touching the orchestrator or the ML layer.

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
- `model/configuracion.py` and `model/retroalimentacion.py` keep their file
  path in a module-level `RUTA` precisely so tests can `monkeypatch.setattr`
  it to a `tmp_path` instead of touching the real `model/arquitectura.json`
  or `model/retroalimentacion.json` — never point a test at the real files
  (see `tests/test_configuracion.py`, `tests/test_retroalimentacion.py` for
  the pattern). `tests/test_orquestador.py` applies this via an `autouse`
  fixture so every test in that file gets an isolated, empty feedback
  queue by default (`model/rag_retroalimentacion.py` is consulted on every
  call, so leaving this unpatched anywhere `/reply` can escalate will
  pollute the real file — this bit a test in `tests/test_rrhh_api.py`
  before the fixture existed; any new test that escalates must patch
  `retroalimentacion.RUTA` too). The real `model/conectores.py` MCP path is
  never exercised in this suite either — its private transport call is
  patched directly (see `tests/test_conectores.py`); an actual MCP server
  is a manual/integration concern, same spirit as the real ML models above.

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
