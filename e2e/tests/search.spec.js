// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh browser page loading dist/index.html with the default
// profile (Valentina, no localStorage set yet). Suggestion chips come in two
// kinds: trámite/feature chips (data-route, navigate on click, keep the " →"
// arrow) and FAQ-answer chips (data-faq-id, open the full answer in a modal
// on click, no navigation, no arrow). Enter is intentionally a no-op --
// every match only acts on an explicit click.

test.describe("Búsqueda predictiva", () => {
  test("typing a known keyword shows a matching suggestion chip", async ({ page }) => {
    // Given: the page has just loaded.
    // When: the visitor types a phrase about certificates.
    // Then: the top suggestion chip mentions 'certificado'.
    await page.goto("/index.html");
    await page.fill("#query", "certificado laboral");
    await expect(page.locator("#matches .chip").first()).toContainText(/certificado/i);
  });

  test("clicking a trámite chip navigates to that feature", async ({ page }) => {
    // Given: "comprobante de pago" ranks the 'nomina' trámite (action chip,
    // data-route) above the FAQ answer with the same score (empirically
    // verified: stable sort keeps the base intent first on ties).
    // When: the visitor clicks that chip.
    // Then: the URL hash becomes #nomina and the payroll dialog opens.
    await page.goto("/index.html");
    await page.fill("#query", "comprobante de pago");
    await page.locator("#matches .chip", { hasText: /n[oó]mina/i }).first().click();
    await expect(page).toHaveURL(/#nomina$/);
    await expect(page.locator("#modal")).toBeVisible();
  });

  test("clicking an FAQ chip shows the full answer in a modal, without navigating", async ({ page }) => {
    // Given: the same query also ranks the FAQ entry "¿Cómo descargo mi
    // comprobante de pago?" (data-faq-id, no "→" arrow).
    // When: the visitor clicks that chip specifically.
    // Then: the modal opens with the full answer text -- but the URL hash
    // does not change (this is a direct show(), not a route navigation).
    await page.goto("/index.html");
    await page.fill("#query", "comprobante de pago");
    const before = page.url();
    await page.locator('#matches [data-faq-id]', { hasText: "¿Cómo descargo mi comprobante de pago?" }).click();
    await expect(page.locator("#modal")).toBeVisible();
    await expect(page.locator("#detail")).toContainText("Abre Nómina, elige uno de los tres períodos");
    expect(page.url()).toBe(before);
  });

  test("no keyword overlap offers to ask the assistant instead of a false chip", async ({ page }) => {
    // Given: the page has loaded.
    // When: the visitor types text with no overlap with any known intent
    // (empirically verified against the real intents/catalogo data).
    // Then: #matches shows the no-match hint plus an explicit "ask the
    // assistant" action -- not a coincidental chip pretending to match.
    await page.goto("/index.html");
    await page.fill("#query", "zzqq wwrr");
    await expect(page.locator("#matches")).toContainText("Sin coincidencias");
    await expect(page.locator("#matches [data-route], #matches [data-faq-id]")).toHaveCount(0);
    await expect(page.locator("#matches [data-ask]")).toBeVisible();
  });

  test("Enter never navigates or opens anything, even with a confident match", async ({ page }) => {
    // Given: "comprobante de pago" produces a confident (score 2) chip.
    // When: the visitor presses Enter instead of clicking anything.
    // Then: nothing happens -- no modal, no navigation. This is also what
    // fixes the original bug report (a greeting like "buenos dias"
    // coincidentally matching "días" in the vacation-balance intent could
    // hijack Enter); disabling Enter entirely removes that whole class of
    // false positive, not just the specific "días" case.
    await page.goto("/index.html");
    await page.fill("#query", "comprobante de pago");
    await page.keyboard.press("Enter");
    await expect(page.locator("#modal")).not.toBeVisible();
    await expect(page).not.toHaveURL(/#nomina$/);
  });

  test("asking the assistant requires clicking the explicit button, not Enter", async ({ page }) => {
    // Given: a query with no keyword match at all.
    await page.route("http://127.0.0.1:5000/reply", route => route.abort());
    await page.goto("/index.html");
    await page.fill("#query", "zzqq wwrr");

    // When: the visitor presses Enter first (should do nothing)...
    await page.keyboard.press("Enter");
    await expect(page.locator("#model-box")).not.toBeVisible();

    // ...then clicks "Preguntar al asistente" explicitly.
    await page.click("#matches [data-ask]");
    await expect(page.locator("#model-box")).toBeVisible();
  });
});
