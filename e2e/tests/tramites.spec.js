// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh page load, default profile (Valentina). These trámites
// mirror real Prebel processes (EPS, créditos de bienestar, prima,
// incapacidades, cesantías, traslado de pensión) handled in reality by named
// HR contacts -- but per CONSTITUTION.md R1, confirmations here only ever
// name the owning department (e.g. "Bienestar y RSE"), never a real person.

test.describe("Trámites con Nómina y Bienestar", () => {
  test("submitting a crédito de educación request registers it under Mis solicitudes", async ({ page }) => {
    // Given: the visitor opens the crédito de educación form (reachable in
    // the real app via the matching FAQ entry's action link).
    await page.goto("/index.html#credito-educacion");
    await expect(page.locator("#modal")).toBeVisible();

    // When: they fill the form and submit it.
    await page.selectOption("#t-destino", { index: 0 });
    await page.fill("#t-monto", "1500000");
    await page.click("#tramite-form button.primary");

    // Then: the confirmation names the department, never a real contact, and
    // the request shows up as Pendiente in Mis solicitudes.
    await expect(page.locator("#detail")).toContainText("Bienestar y RSE");
    await page.click('#modal [data-route="solicitudes"]');
    await expect(page.locator("#detail")).toContainText("Crédito de educación o compra de computador · Pendiente");
  });

  test("reporting an incapacidad can be cancelled from history", async ({ page }) => {
    // Given: the visitor opens the incapacidad report form.
    await page.goto("/index.html#incapacidad-reporte");

    // When: they fill it, submit, and then cancel it from Mis solicitudes.
    await page.fill("#t-fecha_inicio", "2026-11-10");
    await page.fill("#t-dias", "2");
    await page.selectOption("#t-entidad", { index: 0 });
    await page.click("#tramite-form button.primary");
    await page.click('#modal [data-route="solicitudes"]');
    await expect(page.locator("#detail")).toContainText("Reporte de incapacidad médica · Pendiente");
    await page.locator("article.entry", { hasText: "incapacidad" })
      .getByRole("button", { name: "Cancelar solicitud" }).click();

    // Then: its status updates to Cancelada.
    await expect(page.locator("#detail")).toContainText("Reporte de incapacidad médica · Cancelada");
  });

  test("prima view is read-only and shows the current profile's accumulated days", async ({ page }) => {
    // Given: Valentina's mock record has 45 días de prima acumulados
    // (model/empleados_mock.json), consumed via catalogo.js's dias_prima.
    // When: the visitor opens #prima.
    // Then: it shows that number, with no form to submit (it's informational,
    // unlike the other trámites -- prima isn't something you request).
    await page.goto("/index.html#prima");
    await expect(page.locator("#detail")).toContainText("45 días acumulados");
    await expect(page.locator("#detail form")).toHaveCount(0);
  });

  test("every form-backed trámite route actually opens a submittable form", async ({ page }) => {
    // Given: all 9 new trámites except 'prima' (informational) are backed by
    // a real <form>.
    // When: each route is visited directly.
    // Then: the modal opens with a #tramite-form inside it.
    const rutas = [
      "eps-inclusion", "eps-traslado", "credito-educacion", "credito-mascotas",
      "credito-salud", "credito-vivienda", "incapacidad-reporte", "cesantias", "pension-traslado",
    ];
    for (const ruta of rutas) {
      await page.goto("/index.html#" + ruta);
      await expect(page.locator("#modal"), ruta).toBeVisible();
      await expect(page.locator("#tramite-form"), ruta).toBeVisible();
    }
  });
});
