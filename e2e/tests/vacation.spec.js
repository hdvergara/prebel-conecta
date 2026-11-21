// @ts-check
const { test, expect } = require("@playwright/test");

// Context: a fresh page load, default profile (Valentina, saldo: 12 días
// hábiles, per catalogo.py). Dates below are computed relative to "today"
// (not hardcoded calendar dates) because #start/#end carry a native
// min="today" constraint: a past date passes .fill() but silently blocks
// the native form submit, which is exactly what broke this file's first
// version. weekdaysBetween() below mirrors app.js's own weekdays() so the
// day counts are verified by computation, not assumption.

function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}
function iso(date) {
  return date.toISOString().slice(0, 10);
}
function nextWeekday(from, targetDay) {
  // targetDay: 0=Sun .. 6=Sat. Always strictly in the future (never "today").
  const d = new Date(from);
  const diff = ((targetDay - d.getDay() + 7) % 7) || 7;
  return addDays(d, diff);
}
function weekdaysBetween(startIso, endIso) {
  let count = 0;
  for (let d = new Date(startIso + "T12:00:00"); d <= new Date(endIso + "T12:00:00"); d.setDate(d.getDate() + 1)) {
    if (d.getDay() % 6 !== 0) count++;
  }
  return count;
}

test.describe("Solicitud de vacaciones", () => {
  test("a valid weekday range can be requested and appears in Mis solicitudes", async ({ page }) => {
    // Given: the visitor opens the vacation-planning dialog from the services grid.
    await page.goto("/index.html");
    await page.click('a.service[href="#vacaciones"]');
    await expect(page.locator("#modal")).toBeVisible();

    // When: they pick the next Monday-Tuesday (2 business days) and confirm.
    const monday = nextWeekday(new Date(), 1);
    const tuesday = addDays(monday, 1);
    expect(weekdaysBetween(iso(monday), iso(tuesday))).toBe(2);
    await page.fill("#start", iso(monday));
    await page.fill("#end", iso(tuesday));
    await page.click("#dates button.primary");
    await page.click("#send");

    // Then: the request is registered and shows up under "Mis solicitudes".
    await expect(page.locator("#detail")).toContainText("quedó pendiente");
    await page.click('#modal [data-route="solicitudes"]');
    await expect(page.locator("#detail")).toContainText("Vacaciones · Pendiente");
  });

  test("requesting more days than the available balance shows an error", async ({ page }) => {
    // Given: Valentina's available balance is 12 días.
    await page.goto("/index.html");
    await page.click('a.service[href="#vacaciones"]');

    // When: she requests a range spanning well beyond her balance (30
    // calendar days always contains more than 12 business days).
    const monday = nextWeekday(new Date(), 1);
    const end = addDays(monday, 30);
    expect(weekdaysBetween(iso(monday), iso(end))).toBeGreaterThan(12);
    await page.fill("#start", iso(monday));
    await page.fill("#end", iso(end));
    await page.click("#dates button.primary");

    // Then: the form shows the over-balance error instead of advancing to
    // the confirmation step.
    await expect(page.locator("#error")).toContainText("superan tu saldo");
    await expect(page.locator("#send")).toHaveCount(0);
  });

  test("requesting a weekend-only range shows the zero-days error", async ({ page }) => {
    // Given: the next Saturday-Sunday pair contains no business days.
    await page.goto("/index.html");
    await page.click('a.service[href="#vacaciones"]');

    const saturday = nextWeekday(new Date(), 6);
    const sunday = addDays(saturday, 1);
    expect(weekdaysBetween(iso(saturday), iso(sunday))).toBe(0);

    // When: that weekend-only range is submitted.
    await page.fill("#start", iso(saturday));
    await page.fill("#end", iso(sunday));
    await page.click("#dates button.primary");

    // Then: the form rejects it with the "choose at least one weekday" error.
    await expect(page.locator("#error")).toContainText("lunes a viernes");
  });
});
