// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh browser context per test (Playwright default), so
// localStorage starts empty -- exactly "first visit" from the app's own
// perspective (no perfil-demo key saved yet).

test.describe("Selección de perfil", () => {
  test("first visit shows a non-blocking notice instead of assuming silently", async ({ page }) => {
    // Given: no perfil-demo key in localStorage yet.
    // When: the page loads.
    // Then: a dismissible banner says which profile is shown by default and
    // points at the existing "Perfil de demo" selector -- as a plain <p>,
    // not the shared <dialog>, so it never blocks interacting with the rest
    // of the page (unlike a modal, which would).
    await page.goto("/index.html");
    const aviso = page.locator("#perfil-aviso");
    await expect(aviso).toBeVisible();
    await expect(aviso).toContainText("Valentina Ruiz");
    await expect(aviso).toContainText("Perfil de demo");
    await expect(page.locator("#modal")).not.toBeVisible();
  });

  test("dismissing the notice removes it without affecting the page", async ({ page }) => {
    await page.goto("/index.html");
    await page.locator("#perfil-aviso-cerrar").click();
    await expect(page.locator("#perfil-aviso")).toHaveCount(0);
  });

  test("choosing a profile from the existing selector persists it and removes the notice", async ({ page }) => {
    // Given: the first-visit notice is showing.
    await page.goto("/index.html");
    await expect(page.locator("#perfil-aviso")).toBeVisible();

    // When: the visitor picks Camila Torres from "Perfil de demo" (the
    // selector the notice points them to).
    await page.selectOption("#perfil", "camila");

    // Then: the page reloads as Camila, and the notice is gone -- a profile
    // has now been explicitly chosen, so there's nothing left to ask.
    await expect(page.locator("#nombre")).toHaveText("Camila");
    await expect(page.locator("#perfil-aviso")).toHaveCount(0);
  });

  test("a returning visit (profile already chosen) shows no notice", async ({ page }) => {
    // Given: a visitor who already chose a profile on a previous visit.
    await page.goto("/index.html");
    await page.selectOption("#perfil", "mateo");
    await expect(page.locator("#nombre")).toHaveText("Mateo");

    // When: they come back (reload).
    await page.reload();

    // Then: no notice, no modal -- nothing left unasked.
    await expect(page.locator("#perfil-aviso")).toHaveCount(0);
    await expect(page.locator("#modal")).not.toBeVisible();
  });
});
