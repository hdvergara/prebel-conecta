// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh browser page loading dist/index.html with the default
// profile (Valentina, no localStorage set yet).

test.describe("Búsqueda predictiva", () => {
  test("typing a known keyword shows a matching suggestion chip", async ({ page }) => {
    // Given: the page has just loaded.
    // When: the visitor types a phrase about certificates.
    // Then: the top suggestion chip mentions 'certificado'.
    await page.goto("/index.html");
    await page.fill("#query", "certificado laboral");
    await expect(page.locator("#matches .chip").first()).toContainText(/certificado/i);
  });

  test("clicking a suggestion chip navigates to that feature", async ({ page }) => {
    // Given: the visitor has typed a query that produces a 'nomina' chip.
    // When: they click that chip.
    // Then: the URL hash becomes #nomina and the payroll dialog opens.
    await page.goto("/index.html");
    await page.fill("#query", "comprobante de pago");
    await page.locator("#matches .chip", { hasText: /n[oó]mina/i }).first().click();
    await expect(page).toHaveURL(/#nomina$/);
    await expect(page.locator("#modal")).toBeVisible();
  });

  test("no keyword overlap shows the no-match hint, not a false chip", async ({ page }) => {
    // Given: the page has loaded.
    // When: the visitor types text with no overlap with any known intent
    // (empirically verified against the real intents/catalogo data).
    // Then: #matches shows the no-match hint instead of any chip.
    await page.goto("/index.html");
    await page.fill("#query", "zzqq wwrr");
    await expect(page.locator("#matches")).toContainText("Sin coincidencias");
    await expect(page.locator("#matches .chip")).toHaveCount(0);
  });

  test("pressing Enter with a confident (2+ word) match activates that chip", async ({ page }) => {
    // Given: "comprobante de pago" matches 2 words against the 'nomina'
    // intent (empirically verified) -- a confident, non-coincidental match.
    // When: the visitor presses Enter without clicking it explicitly.
    // Then: the top chip's route is activated, same as a click would do.
    await page.goto("/index.html");
    await page.fill("#query", "comprobante de pago");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#nomina$/);
    await expect(page.locator("#modal")).toBeVisible();
  });

  test("a greeting that coincidentally shares one word doesn't hijack Enter", async ({ page }) => {
    // Given: "buenos dias" scores exactly 1 point against several intents
    // (saldo, prediccion, ...) purely because "dias" is a keyword in all of
    // them -- a coincidental, single-word match, not real intent.
    // When: the visitor presses Enter.
    // Then: Enter does NOT silently open an unrelated feature (e.g. the
    // vacation-balance dialog); it defers to the semantic model instead,
    // which is reachable precisely because no chip was confidently clicked.
    await page.route("http://127.0.0.1:5000/reply", route => route.abort());
    await page.goto("/index.html");
    await page.fill("#query", "buenos dias");
    await page.keyboard.press("Enter");
    await expect(page.locator("#modal")).not.toBeVisible();
    await expect(page).not.toHaveURL(/#saldo$/);
    await expect(page.locator("#model-box")).toBeVisible();
  });
});
