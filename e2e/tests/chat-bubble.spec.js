// @ts-check
const { test, expect } = require("@playwright/test");

// Context: the portal-side "Puerta Web" (n8n chat bubble, Tier 2 of the
// Predictive -> ML -> Agentic chain, see CONSTITUTION.md) must never load
// for a plain visitor -- the n8n server behind it answers one AI question
// at a time. It's gated two ways: the ?chat=demo URL flag, AND
// CHAT_WEBHOOK_URL shipping as an unfilled "[...]" placeholder until the
// team configures a real one (R5 bracket-placeholder convention). These
// tests only cover that gating -- there's no real n8n Chat Trigger to talk
// to in this suite, so the actual conversation is out of scope here.

test.describe("Puerta Web (burbuja de chat)", () => {
  test("never attempts to load the chat widget without the demo flag", async ({ page }) => {
    await page.goto("/index.html");
    await expect(page.locator('link[href*="@n8n/chat"]')).toHaveCount(0);
  });

  test("still does not load with the demo flag, while the webhook URL is an unconfigured placeholder", async ({ page }) => {
    // Given: the shipped CHAT_WEBHOOK_URL is still "[URL del Chat Trigger...]".
    // When: a visitor loads the portal with ?chat=demo anyway.
    // Then: nothing loads -- safe by default until the team fills in a real
    // URL, even if someone guesses or leaks the flag.
    await page.goto("/index.html?chat=demo");
    await expect(page.locator('link[href*="@n8n/chat"]')).toHaveCount(0);
  });

  test("the rest of the portal is unaffected by the ?chat=demo flag", async ({ page }) => {
    // R2: this flag must never change or block anything else on the page.
    await page.goto("/index.html?chat=demo");
    await expect(page.locator("#nombre")).not.toBeEmpty();
    await expect(page.locator("#modal")).not.toBeVisible();
  });
});
