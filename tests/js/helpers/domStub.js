"use strict";
// Minimal DOM/BOM stub for running dist/app.js logic under Node's vm module.
// Not a browser: no real rendering, no real layout. Used only to exercise
// app.js's pure top-level functions (ownerLabel, rank, weekdays, ...) for
// the JS unit tests in app.test.js. Real browser behavior is covered by the
// Playwright e2e suite in prebel-conecta/e2e/ instead.
const vm = require("node:vm");

function makeEl(tag) {
  const el = {
    tagName: tag,
    children: [],
    attrs: {},
    classList: { add() {}, remove() {} },
    style: {},
    get className() { return this.attrs["class"] || ""; },
    set className(v) { this.attrs["class"] = v; },
    set textContent(v) { this._text = v; },
    get textContent() { return this._text || ""; },
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html || ""; },
    append(...kids) { this.children.push(...kids); },
    appendChild(k) { this.children.push(k); return k; },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k]; },
    add(opt) { this.children.push(opt); },
    querySelector(sel) { return this.children.find(c => c.tagName === sel) || null; },
    querySelectorAll() { return []; },
    scrollIntoView() {},
    focus() {},
    closest() { return null; },
    addEventListener() {},
    get value() { return this._value || ""; },
    set value(v) { this._value = v; },
    open: false,
    showModal() { this.open = true; },
    close() { this.open = false; },
    get hidden() { return this._hidden; },
    set hidden(v) { this._hidden = v; },
  };
  return el;
}

const KNOWN_IDS = [
  "perfil", "nombre", "puesto", "faq-list", "query", "matches", "balance", "modal", "detail",
  "close", "services", "start", "end", "dates", "error", "edit", "send", "estimate", "months",
  "period", "pay", "download", "type", "generate",
  "model-box", "model-query", "model-quick", "model-answer", "model-confidence",
  "model-sentiment", "model-owner", "model-action",
];

/**
 * Loads catalogo.js + faq.js + app.js (from distDir) into a fresh vm context
 * with DOM/BOM stubs. Returns { ctx, elements } so a test can inspect stub
 * elements directly or run further snippets via run(ctx, code) that reference
 * app.js's top-level consts/functions as bare identifiers.
 */
function loadApp(fs, path, distDir, { fetchImpl } = {}) {
  const elements = {};
  KNOWN_IDS.forEach(id => { elements[id] = makeEl(id); });

  const storage = {};
  const sandbox = {
    console,
    document: {
      getElementById: id => elements[id] || (elements[id] = makeEl(id)),
      createElement: tag => makeEl(tag),
      addEventListener: () => {},
    },
    window: {},
    localStorage: {
      getItem: k => (k in storage ? storage[k] : null),
      setItem: (k, v) => { storage[k] = String(v); },
    },
    location: { hash: "" },
    crypto: { randomUUID: () => "test-uuid" },
    URL: { createObjectURL: () => "blob:test", revokeObjectURL: () => {} },
    Blob: function Blob() {},
    fetch: fetchImpl || (() => Promise.reject(new Error("no fetch in this test"))),
    AbortController: function AbortController() { this.signal = {}; this.abort = () => {}; },
    setTimeout,
    clearTimeout,
    Option: function Option(text, value) { this.text = text; this.value = value; },
  };
  sandbox.window.addEventListener = () => {};
  sandbox.globalThis = sandbox;

  const ctx = vm.createContext(sandbox);
  for (const file of ["catalogo.js", "faq.js", "app.js"]) {
    vm.runInContext(fs.readFileSync(path.join(distDir, file), "utf8"), ctx, { filename: file });
  }
  return { ctx, elements };
}

function run(ctx, code) {
  return vm.runInContext(code, ctx, { filename: "inline.js" });
}

module.exports = { loadApp, run };
