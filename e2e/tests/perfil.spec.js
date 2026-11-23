// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh browser context per test (Playwright default), so
// localStorage starts empty -- exactly "first visit" from the app's own
// perspective (no perfil-demo key saved yet).

test.describe("Selección de perfil", () => {
  test("first visit asks for the Personal ID, instead of assuming an identity silently", async ({ page }) => {
    // Given: no perfil-demo key in localStorage yet.
    // When: the page loads.
    // Then: a dismissible banner asks for the visitor's número de documento
    // (Personal ID), says which profile is shown meanwhile, and points at
    // the existing "Perfil de demo" selector as an alternative -- as a
    // plain <p>, not the shared <dialog>, so it never blocks interacting
    // with the rest of the page (unlike a modal, which would).
    await page.goto("/index.html");
    const aviso = page.locator("#perfil-aviso");
    await expect(aviso).toBeVisible();
    await expect(aviso).toContainText("número de documento");
    await expect(aviso).toContainText("Valentina Ruiz");
    await expect(aviso).toContainText("Perfil de demo");
    await expect(page.locator("#perfil-aviso-id")).toBeVisible();
    await expect(page.locator("#modal")).not.toBeVisible();
  });

  test("entering a known Personal ID identifies and persists that profile", async ({ page }) => {
    // Given: the first-visit notice is showing.
    await page.goto("/index.html");

    // When: the visitor types Camila Torres's mock documento (from
    // model/empleados_mock.json) and clicks Entrar.
    await page.fill("#perfil-aviso-id", "1000000003");
    await page.click("#perfil-aviso-entrar");

    // Then: the page reloads identified as Camila, and the notice is gone.
    await expect(page.locator("#nombre")).toHaveText("Camila");
    await expect(page.locator("#perfil-aviso")).toHaveCount(0);
  });

  test("pressing Enter in the Personal ID field submits it too", async ({ page }) => {
    await page.goto("/index.html");
    await page.fill("#perfil-aviso-id", "1000000004");
    await page.locator("#perfil-aviso-id").press("Enter");
    await expect(page.locator("#nombre")).toHaveText("Andrés");
  });

  test("an unknown Personal ID shows an error and does not change profile", async ({ page }) => {
    // Given: the first-visit notice is showing.
    await page.goto("/index.html");

    // When: the visitor types a document number that matches no mock
    // employee.
    await page.fill("#perfil-aviso-id", "9999999999");
    await page.click("#perfil-aviso-entrar");

    // Then: an error shows, the page does not reload, and the notice (with
    // the default Valentina) is still there to try again.
    await expect(page.locator("#perfil-aviso-error")).toContainText("No encontramos ese número de documento");
    await expect(page.locator("#perfil-aviso")).toBeVisible();
    await expect(page.locator("#nombre")).toHaveText("Valentina");
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
