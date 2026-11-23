// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh page load. FAQ entries sourced from the semantic model
// (dist/faq.js, generated from model/faq_rrhh.json) are merged into the same
// #faq-list as the hardcoded ones, each carrying an optional ruta/area.

test.describe("Preguntas frecuentes (modelo)", () => {
  test("a model FAQ entry without a feature route shows no action link", async ({ page }) => {
    // Given: the 'datos personales' entry (faq-modelo-4) has ruta: null in
    // model/faq_rrhh.json (unlike 'incapacidad', which now routes to its own
    // report form and so is excluded from this case).
    // When: the visitor navigates directly to #faq-modelo-4.
    // Then: that <details> opens and shows an owner label, but no <a> link
    // (nothing to route to -- R2 in CONSTITUTION.md: no dangling actions).
    await page.goto("/index.html#faq-modelo-4");
    const item = page.locator("#faq-modelo-4");
    await expect(item).toHaveJSProperty("open", true);
    await expect(item.locator("p.muted")).toContainText("Gestión Humana");
    await expect(item.locator("a")).toHaveCount(0);
  });

  test("a model FAQ entry with a feature route shows a working action link", async ({ page }) => {
    // Given: the 'vacaciones' entry (faq-modelo-0) has ruta: 'vacaciones'.
    // When: the visitor opens it directly via hash and clicks its action link.
    // Then: the vacation-planning dialog opens.
    await page.goto("/index.html#faq-modelo-0");
    await page.locator("#faq-modelo-0 a").click();
    await expect(page).toHaveURL(/#vacaciones$/);
    await expect(page.locator("#modal")).toBeVisible();
  });

  test("visiting an unknown hash closes the modal instead of erroring", async ({ page }) => {
    // Given: a hash that matches neither a FAQ id, a catalogo resource, nor
    // a feature route.
    // When: the page loads with that hash.
    // Then: nothing crashes and the modal stays closed.
    await page.goto("/index.html#no-existe-esta-ruta");
    await expect(page.locator("#modal")).not.toBeVisible();
  });
});
