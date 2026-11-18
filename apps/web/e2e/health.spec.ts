import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const [locale, heading, ok] of [
  ["en", "System status", "✓ OK"],
  ["hi", "सिस्टम की स्थिति", "✓ ठीक है"],
] as const) {
  test(`health page works and is accessible in ${locale}`, async ({ page }) => {
    await page.goto(`/${locale}`);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    // The database row reports OK only when the API really reached Postgres.
    await expect(page.getByRole("cell", { name: ok }).first()).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    expect(serious, JSON.stringify(serious.map((v) => v.id))).toEqual([]);
  });
}

test("root redirects to the English page", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/en$/);
});
