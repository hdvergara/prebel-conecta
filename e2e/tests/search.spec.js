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

  test("pressing Enter with a visible chip activates that chip", async ({ page }) => {
    // Given: a query whose top-ranked chip is the 'saldo' feature itself
    // (empirically verified; many queries rank a richer FAQ phrasing above
    // the base feature, which this test deliberately avoids).
    // When: the visitor presses Enter without clicking it explicitly.
    // Then: the top chip's route is activated, same as a click would do.
    await page.goto("/index.html");
    await page.fill("#query", "proyectar mi saldo");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#saldo$/);
    await expect(page.locator("#modal")).toBeVisible();
  });
});
