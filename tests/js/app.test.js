"use strict";
// Unit tests for app.js's pure helper functions, run under Node's vm module
// (no browser). Per CONSTITUTION.md "Harness": these cover logic only --
// real rendering/interaction is covered by the Playwright e2e suite.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { loadApp, run } = require("./helpers/domStub");

const DIST = path.resolve(__dirname, "../../dist");

// Context: dist/app.js loaded fresh (via vm) for each test, against the
// real catalogo.js/faq.js data (the app's actual static dataset).

test("ownerLabel returns the parent-prefixed label for a sub-area", () => {
  // Given: 'nomina' is a sub-area of 'gh' in catalogo.js.
  // When: ownerLabel('nomina') is called.
  // Then: it returns 'Gestión Humana · Nómina'.
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "ownerLabel('nomina')"), "Gestión Humana · Nómina");
});

test("ownerLabel returns the plain label for a top-level area", () => {
  // Given: 'gh' has no parent area.
  // When: ownerLabel('gh') is called.
  // Then: it returns just 'Gestión Humana', with no '·' prefix.
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "ownerLabel('gh')"), "Gestión Humana");
});

test("ownerLabel returns null for a falsy area id", () => {
  // Given: an FAQ entry with no area (e.g. the original hardcoded ones).
  // When: ownerLabel(undefined) is called.
  // Then: it returns null, so app.js renders no owner tag at all.
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "ownerLabel(undefined)"), null);
});

test("rank() puts the richer FAQ phrasing above the shorter base intent", () => {
  // Given: 'necesito un certificado laboral' matches 3 words in the model
  // FAQ entry's full phrasings but only 2 in the shorter base 'certificado'
  // intent (empirically verified against the real intents/faq data).
  // When: rank() is called with that query.
  // Then: the richer match (faq-modelo-1) ranks first.
  const { ctx } = loadApp(fs, path, DIST);
  const top = run(ctx, "rank('necesito un certificado laboral')[0]");
  assert.equal(top.id, "faq-modelo-1");
  assert.equal(top.score, 3);
});

test("rank() returns an empty array for text with no keyword overlap", () => {
  // Given: a query that shares no keyword with any intent.
  // When: rank() is called.
  // Then: it returns an empty array (no false-positive suggestion).
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "rank('zzqq wwrr').length"), 0);
});

test("weekdays counts only Mon-Fri inclusive of both endpoints", () => {
  // Given: 2026-11-16 is a Monday and 2026-11-20 is a Friday.
  // When: weekdays() is called across that span.
  // Then: it returns 5 (every weekday counted once, weekends excluded).
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "weekdays('2026-11-16', '2026-11-20')"), 5);
});

test("weekdays excludes a weekend at the edges of the range", () => {
  // Given: 2026-11-14 (Sat) to 2026-11-16 (Mon).
  // When: weekdays() is called.
  // Then: only the Monday counts, so the result is 1.
  const { ctx } = loadApp(fs, path, DIST);
  assert.equal(run(ctx, "weekdays('2026-11-14', '2026-11-16')"), 1);
});

test("the model FAQ entries are merged into preguntas with unique ids", () => {
  // Given: app.js merges faqModel.faq (6 entries) into the hardcoded
  // preguntas list.
  // When: the script finishes loading.
  // Then: every pregunta.id is unique -- a duplicate id would break the FAQ
  // accordion (duplicate DOM ids) and the hash-router's lookup.
  const { ctx } = loadApp(fs, path, DIST);
  const ids = run(ctx, "preguntas.map(p => p.id)");
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.length >= 10);
});

test("sentimentLabel reports the API-unavailable message for a null sentiment", () => {
  // Given: modelReply()'s catch path passes sentimiento: null when the local
  // API is unreachable.
  // When: sentimentLabel(null) is called.
  // Then: it returns the explicit 'not available' message, not a crash.
  const { ctx } = loadApp(fs, path, DIST);
  assert.match(run(ctx, "sentimentLabel(null)"), /No disponible/);
});

test("sentimentLabel formats a real sentiment with its emoji and percentage", () => {
  // Given: a sentiment object as the API would return it.
  // When: sentimentLabel() formats it.
  // Then: it includes the label and the rounded percentage.
  const { ctx } = loadApp(fs, path, DIST);
  const label = run(ctx, "sentimentLabel({etiqueta:'positivo', estrellas:5, confianza:0.79})");
  assert.match(label, /positivo/);
  assert.match(label, /79%/);
});
