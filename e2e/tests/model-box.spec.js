// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh page load. Every test in this file intercepts the local
// model API (MODEL_API = http://127.0.0.1:5000/reply) via page.route(), per
// CONSTITUTION.md "Harness": e2e must not depend on a real Flask backend or
// the real ~1GB ML models being installed. The query text 'zzqq wwrr' is
// empirically verified (see search.spec.js) to produce zero suggestion
// chips, so Enter reliably falls through to askAssistant() in both tests.

test.describe("Cuadro de resultado del modelo", () => {
  test("a mocked semantic match renders the full comparison box", async ({ page }) => {
    // Given: the local API is mocked to return a confident vacaciones match.
    await page.route("http://127.0.0.1:5000/reply", route => route.fulfill({
      json: {
        reply: "Envía la solicitud a tu jefe directo...",
        ruta: "vacaciones",
        area: "gh",
        confianza: 0.91,
        sentimiento: { etiqueta: "positivo", estrellas: 5, confianza: 0.8 },
      },
    }));
    await page.goto("/index.html");

    // When: the visitor types a free-text question with no chip match and
    // presses Enter, so askAssistant() calls the (mocked) model directly.
    await page.fill("#query", "zzqq wwrr");
    await page.keyboard.press("Enter");

    // Then: the response box becomes visible with the mocked answer, 91%
    // confidence, the sentiment label, the owning department, and a working
    // action link bound to the matched route.
    await expect(page.locator("#model-box")).toBeVisible();
    await expect(page.locator("#model-answer")).toContainText("Envía la solicitud");
    await expect(page.locator("#model-confidence")).toHaveText("91%");
    await expect(page.locator("#model-sentiment")).toContainText("positivo");
    await expect(page.locator("#model-owner")).toContainText("Gestión Humana");
    // 'zzqq wwrr' has no keyword-based match (that's exactly why Enter
    // reached askAssistant instead of clicking a chip), so the quick-match
    // field must say so rather than show a stale or fabricated value.
    await expect(page.locator("#model-quick")).toHaveText("Sin coincidencia rápida");
    await page.locator("#model-action button").click();
    await expect(page).toHaveURL(/#vacaciones$/);
  });

  test("an unreachable local API degrades to the static fallback message", async ({ page }) => {
    // Given: the local API route is aborted, simulating "API not running"
    // (R2 in CONSTITUTION.md: the static layer must never hard-depend on it).
    await page.route("http://127.0.0.1:5000/reply", route => route.abort());
    await page.goto("/index.html");

    // When: the visitor asks a free-text question with no chip match.
    await page.fill("#query", "zzqq wwrr");
    await page.keyboard.press("Enter");

    // Then: the box still appears, but confidence/sentiment explicitly say
    // "not available" and the answer is the FAQ model's own static fallback
    // text (dist/faq.js) -- not a crash, not a blank box, not a hang.
    await expect(page.locator("#model-box")).toBeVisible();
    await expect(page.locator("#model-confidence")).toContainText("No disponible");
    await expect(page.locator("#model-sentiment")).toContainText("No disponible");
    await expect(page.locator("#model-answer")).toContainText("rrhh@tuempresa.com");
    await expect(page.locator("#model-action button, #model-action a")).toHaveCount(0);
  });
});
