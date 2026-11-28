# Prebel Conecta — Constitution

The contract for anyone (human or agent) changing this project. It is
**level 0** of the documentation: it holds rules only.

## 0. How to read and change this document

### Documentation levels

Each level may rely on the levels above it. It must never contradict them or
create rules of its own.

| Level | Where | Holds |
|---|---|---|
| 0 — Rules | this file | Rules with an ID |
| Specifications | [`especificaciones/`](especificaciones/README.md) | What each domain context must do: language, boundaries and acceptance scenarios with their evidence. It cites rules and creates none |
| 1 — Behaviour | [`FLUJOS.md`](FLUJOS.md) | What the code does today, including known gaps against these rules |
| 2 — Operation | [`README.md`](README.md), [`SETUP_AND_DEPLOY.md`](SETUP_AND_DEPLOY.md), [`n8n/README.md`](n8n/README.md), `MODEL_*.md` | How to install, run and test |
| Data | `model/arquitectura.json` | The only source of the orchestrator's thresholds |
| Record | [`DECISIONES.md`](DECISIONES.md) | Why a rule is what it is, with its status |
| Open requirements | [`REQUERIMIENTOS_ABIERTOS.md`](REQUERIMIENTOS_ABIERTOS.md) | What is unconfirmed, undecided, unimplemented or unverified. It creates no rule and permits nothing |

A file that is not versioned is never a source: nothing in the repository may
cite it. A PR description or a local plan that conflicts with this file is the
one that is wrong.

### Data-agnostic presumption

What sits behind a backend cannot be known from this repository: a deployment
may change its FAQ, documents, connector or queue. So no rule or control about
**who may reach a surface** may depend on what the data is. When deciding that,
treat the data behind any backend as sensitive: "it is only demo data" opens
nothing. The presumption decides who reaches a surface, not what a surface may
do in controlled conditions; there R7 applies to the data it actually serves.

This is about running surfaces. Versioned content can be reviewed before it is
committed, and R1, R4 and R5 govern it.

### Precedence

Precedence never settles a contradiction between rules: R0 forbids it, and the
text must be fixed. It only says what to protect in the meantime, if a
situation nobody foresaw makes two rules impossible to meet. This is the
normative hierarchy of R0: the lower class number weighs more.

1. **Data protection:** R1, R3, R4, R5, R6, R7, R11.
2. **Availability:** R2, R8.
3. **Demo behaviour and engineering:** R9, R10, R12, R13, R14.

An exception exists only if the rule itself states it.

### Changing a rule

Every change to this document follows R0.

### Terms

- **MVP phase:** the current phase. It lasts until
  [`DECISIONES.md`](DECISIONES.md) records that the environments are defined.
- **API:** the `/reply` endpoint of `model/rrhh_api.py`.
- **Answer surface:** anything that receives a question and answers it from a
  backend: the API, the WhatsApp bridge, every n8n entry point, and any proxy
  or chat widget leading to one.
- **Controlled conditions:** a surface is reachable only from the operator's
  machine or a private network with known participants, **or** behind access
  control.
- **Access control:** a check made on the server that verifies who is asking and
  authorizes them before the question is processed.
- **Connector:** the interface through which the API reaches a language model.
- **Queue:** the stored question/answer pairs produced through the connector.
- **Generated text:** any answer written by a language model, including one
  reused from the queue.

## 1. Spec

Prebel Conecta is a **demo HR portal**: a static site, a local semantic API, a
local WhatsApp bridge, and a separate n8n system run on the team's server. How
each one behaves is described in level 1.

## 2. Rules

### R0 — Transitivity safeguard
- **Subjects:** every rule, every document, every citation.
- **Principle:** **C must not contradict A through conceptual transitivity in
  B.**
- **Conceptual transitivity:** A reaches C through B when B shares a concept
  with each of them (data, identity, exposure, waiting, a placeholder), even if
  A and C share no word, subject or citation. B may be a rule, a definition, a
  decision, a behaviour described in level 1, or a file that cites a rule.
  Chains may be longer than three links. The order or numbering in which rules
  are written is irrelevant: only the conceptual chain counts.
- **Indirect conflict:** a base A leads to a bridge rule B; the wording of B
  enables C; C negates A. B is then **conditionally inconsistent**: not false by
  itself, but badly delimited. A formal example is in
  [`DECISIONES.md`](DECISIONES.md#ejemplo-formal-de-r0).
- **Rule:** applying A and then B must never require, permit or assume
  something that C forbids, nor leave without support something that C relies
  on. This holds for rules among themselves, and for every lower level against
  them.
- **A change that breaks the principle is not valid** until the chain is
  resolved by changing a rule or what relies on it. Precedence does not resolve
  it, and neither does deleting a citation while the behaviour it justified
  remains.
- **Two tools, at two different moments:**
  1. **Defeasibility fixes the text.** The badly delimited link, normally the
     bridge B, gets an exception written in that rule: B applies except where
     applying it would activate C against A. This is what can make a change
     valid.
  2. **Normative hierarchy blocks execution.** Until the text is fixed, or when
     an unforeseen collision appears, the weight given by the precedence of §0
     lets the heavier rule block what negates it. With equal weight, the action
     that negates the premise is not carried out. Blocking protects; it does not
     make the text consistent, and the change stays invalid. A blocked step
     still falls back as R8 requires.
- **Procedure,** before changing or adding a rule or definition:
  1. List the concepts it touches, including the ones it stops covering.
  2. Follow each concept through rules, definitions, decisions, level 1 and
     every file citing an affected rule, until no new link appears.
  3. For each chain, state what its links force together and check it against
     every rule in the chain.
  4. A norm that something relies on may leave a rule only if another rule takes
     it over, or the reliance is removed in the same change.
  5. Record the chains in the matrix in [`DECISIONES.md`](DECISIONES.md), then
     update `tests/trazabilidad.json`. A chain with no resolution is recorded as
     such, and the change that introduced it is not merged.
- **Not covered:** code that does not yet meet a rule is not a contradiction
  between texts; it is a known gap (R13).
- **Exception:** none.

### R1 — Public repository
- **Subjects:** real data, repository.
- **Rule:** the repository is public. It must never contain real personal data
  (employee names, phone numbers, personal or corporate e-mails, salaries) or
  policy figures taken from internal Prebel documents. This covers every
  versioned file, n8n workflow exports included. The real source documents
  (`.specs/`, `specs/`, `n8n/data/`, `n8n/insumos/`) stay ignored by git.
  Before a commit that touches `model/` or `n8n/`, or adds content, check the
  diff for phone numbers, corporate e-mails and real full names.
- **Exception:** none.

### R2 — Static first
- **Subjects:** portal, API, waiting time.
- **Rule:** nothing in `dist/` may require the API, or any other backend, to
  render or to complete its core flows. Every call to a backend has a fallback
  that works without it, and a bounded wait that does not block the interface.
- **Consequence:** a slow answer may be unavailable to the portal. That is an
  accepted limit; lengthening the wait must not block the interface.

### R3 — No secrets in client code
- **Subjects:** portal, URLs, secrets.
- **Rule:** `dist/` reaches every visitor. It must never hold keys, tokens or
  non-public URLs. The default API address is the visitor's own machine. A
  deployer may override it with `window.PREBEL_MODEL_API`, defined before
  `app.js` loads, in the deployed copy only.
- **Limit:** pointing the override at an API makes that API an answer surface
  for whoever can open the page, so R11 applies.

### R4 — Fictitious demo people
- **Subjects:** demo data.
- **Rule:** people and organisational data used by the portal and the local
  channel are fictitious and stay that way, even for a better demo.

### R5 — Placeholders and demo values
- **Subjects:** FAQ, configuration, demo data, real data.
- **Placeholders:** in any versioned file, a value in brackets (`[X]`,
  `[sistema]`, `[URL ...]`) is one deliberately left unset. Code must treat a
  configuration value still in brackets as not configured and keep the feature
  off.
- **FAQ values:** a value in `model/faq_rrhh.json` is either a placeholder or a
  **fictitious example value**. A fictitious value is allowed only when it is
  introduced on purpose, said to be fictitious in the commit, and shown as an
  example in the answer the user reads (`ejemplo`). It must not be derived from
  real documents.
- **On hold:** the permission for fictitious values is not used until the team
  confirms it in [`DECISIONES.md`](DECISIONES.md). Until then, FAQ values stay
  as placeholders.
- **Real values never enter the repository** (R1). A deployment that needs them
  keeps them outside it.
- **Exception:** none.

### R6 — Channel secrets
- **Subjects:** secrets, WhatsApp bridge.
- **Rule:** connection parameters and secrets of the WhatsApp bridge come from
  environment variables or `.env`, never from versioned code. `.env` stays
  ignored; after editing `.gitignore`, confirm it with
  `git check-ignore -v .env`. `.env.example` holds placeholders that only work
  against a local emulator.

### R7 — Sender identification is not authentication
- **Subjects:** personal data, WhatsApp bridge.
- **Rule:** matching a phone number, or a document number typed in the chat, is
  basic identification: anyone who claims it sees that data. It must never be
  described as secure, or extended to anything sensitive (salary, documents,
  changing data) without real verification added as an explicit step. It is
  therefore not access control (R11).

### R8 — Tier order and graceful fallback
- **Subjects:** answer chain, API, connector, availability.
- **Rule:** in any answer chain, cheaper and faster tiers are tried before
  slower and heavier ones. Every escalation falls back: if the next tier is
  missing, fails or does not answer, the chain returns what it already has, or
  an explicit message. No tier is a hard dependency.
- **Note:** reusing a queued answer is part of the escalation step, not a tier.
  A caller's explicit request to continue may skip the confidence thresholds,
  never the fallback.

### R9 — Layer separation
- **Subjects:** code structure, connector.
- **Rule:** three responsibilities stay apart. **Matching**
  (`model/rrhh_bot.py`) produces the match that both the predictive and the ML
  decisions read. **Deciding** (`model/orquestador.py`) is the only module that
  imports the connector and the queue reuse. **Reaching a model** at answer
  time happens only through the connector interface.
- Matching never imports deciding, the connector or the reuse. The reuse
  receives the embedding model by injection.
- **Out of scope:** offline tooling (`model/entrenar.py`) and the n8n system,
  which is external to the Python chain.

### R10 — One role for n8n, and honest answers
- **Subjects:** n8n, API, generated text.
- **Rule:** in one deployment, an n8n brain is **either** a channel that calls
  the API, **or** a backend behind the connector with an entry point that never
  calls the API. Never both: that closes a loop.
- A consumer of the API must not present generated text as a pre-written FAQ
  answer. It tells the user an AI wrote it, or does not use it.

### R11 — Exposure of answer surfaces
- **Subjects:** answer surfaces, API, n8n, WhatsApp bridge, URLs, real data,
  access control.
- **Rule:** an answer surface runs only in controlled conditions. It must never
  be reachable by an uncontrolled caller, whatever its data, connector or queue
  hold.
- **Not access control, alone or combined:** allowed origins, a URL parameter,
  an unpublished address, a platform signature or webhook secret (they
  authenticate the platform, not the person asking), and the identification of
  R7.
- **Published static content** is generated only from versioned files.
- **Exception, MVP cross-origin:** during the MVP phase, no rule requires
  restricting which origins may call the API from a browser, because the
  environments are not defined and operate across each other. A call made by
  the browser of a participant already inside controlled conditions counts as
  that participant's, whatever page started it.
  - It relaxes the origin only. Who can reach the surface, and access control,
    do not change. It does not depend on what the data is.
  - Cross-origin access must not allow credentials: otherwise any page could use
    a participant's session, which would void access control.
  - **Accepted risk:** another page open in a participant's browser can call the
    API, read its answers and ask it to continue, which can reach the connector
    and fill the queue.
  - It ends when [`DECISIONES.md`](DECISIONES.md) records the environments as
    defined. R11 is then amended under R0.

## 3. Harness

### R12 — Verification
- **Subjects:** tests.
- **Rule:** "done" means the three suites are green: Python
  (`pytest tests`), JavaScript (`node --test tests/js`) and end to end
  (Playwright, in `e2e/`). How to run them is in
  [`README.md`](README.md#tests).
- Unit tests use no network and no real model weights. End-to-end tests
  intercept every call to the API, so they pass without a backend.
- A cohesion check that needs the list of repository files may skip where there
  is no git checkout, such as an exported copy. A skipped check is not green:
  "done" requires it to run in a git checkout.
- No test writes to a real data or state file: it redirects the module's path
  to a temporary one. Anything needing a real model or server is a manual
  integration check, and the PR says whether it was done.
- Each end-to-end test documents Context / Given / When / Then.

### R13 — Documentation cohesion
- **Subjects:** documentation.
- **Rule:** each fact has one home, at its level; other documents link to it.
  A change that alters behaviour updates level 1 in the same PR. A rule the code
  does not meet yet is listed as a known gap in level 1, never silently
  rewritten to match the code. `tests/test_documentacion.py` checks what a
  machine can: links, cited rule IDs, citations of unversioned drafts and
  threshold values. It also fails when a rule's text, or the set of files citing
  it, differs from `tests/trazabilidad.json`, which forces the R0 procedure. It
  cannot find a conceptual chain or prove the review was done well.

### R14 — Specification first
- **Subjects:** behaviour changes, specifications, tests.
- **Rule:** a change to the behaviour of a domain context states it as scenarios
  in that context's specification, before the code or in the same PR. Each
  scenario cites its evidence: an existing automated test, or a requirement,
  open while it is not implemented or tested, or closed when its closure records
  a manual check (R12). A scenario describes; it permits nothing a rule forbids.
- **Exception:** reducing exposure, such as taking an answer surface offline or
  tightening access to meet R1 or R11, never waits for this rule. The
  specification is updated afterwards.
