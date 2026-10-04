import { expect, test } from "@playwright/test";

test("upload once → map → validate → import → analyze → scoped investigation", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/datasets");
  await page.getByRole("button", { name: "Add Dataset", exact: true }).click();
  await page.getByLabel("CSV file").setInputFiles({ name: "product-fixture.csv", mimeType: "text/csv", buffer: Buffer.from("body,when,network,likes\nOpenAI model research,2026-09-01T10:00:00Z,twitter,0\nOpenAI model research,2026-09-02T10:00:00Z,reddit,5\nOpenAI model research,2026-09-03T10:00:00Z,twitter,10\nGoogle model research,2026-09-03T11:00:00Z,youtube,3\nInvalid date example,invalid,twitter,0\n") });
  await page.getByRole("button", { name: "Upload and preview", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Raw CSV preview" })).toBeVisible();
  await page.getByRole("combobox", { name: /^Text column/ }).selectOption("body");
  await page.getByRole("combobox", { name: /^Timestamp column/ }).selectOption("when");
  await page.getByRole("button", { name: "Confirm mapping" }).click();
  await expect(page.getByRole("button", { name: "Validate CSV" })).toBeEnabled();
  await page.getByRole("button", { name: "Validate CSV" }).click();
  await expect(page.getByText("4 valid · 1 invalid · 2 duplicates retained and flagged")).toBeVisible();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Import valid rows" }).click();
  await expect(page.getByRole("heading", { name: "Imported posts preview" })).toBeVisible();
  await page.getByRole("button", { name: "Run Analysis", exact: true }).click();
  await page.getByRole("link", { name: "Open Dashboard", exact: true }).first().click({ timeout: 90000 });
  await expect(page.getByRole("heading", { name: "What changed, and why?" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ranked trends" })).toBeVisible();
  await expect(page).toHaveURL(/dataset=.+&run=.+/);
  await page.getByRole("link", { name: "All trends & topics →" }).click();
  await expect(page.getByRole("heading", { name: /matching topics/ })).toBeVisible();
  await page.locator(".trend-table tbody th a").first().click();
  await expect(page.getByRole("heading", { name: "Representative posts" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Trend history" })).toBeVisible();
  await page.getByRole("link", { name: "Explore all assigned posts →" }).click();
  // Search the whole selected run; learned clusters need not match fixture clusters.
  await page.getByRole("combobox", { name: /^Topic/ }).selectOption("");
  await page.getByLabel("Keyword", { exact: true }).fill("OpenAI");
  await page.getByRole("button", { name: "Search posts" }).click();
  await expect(page.getByRole("heading", { name: "3 matching posts" })).toBeVisible();
  await page.getByRole("link", { name: "Analysis", exact: true }).click();
  await expect(page.getByRole("heading", { name: "TrendScore and classification" })).toBeVisible();
  if (process.env.E2E_REAL_NLP === "1") {
    await page.screenshot({ path: "../.verification/real-analysis-page.png", fullPage: true });
    await page.getByRole("link", { name: "Dashboard", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Ranked trends" })).toBeVisible();
    await page.screenshot({ path: "../.verification/real-dashboard.png", fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByRole("heading", { name: "What changed, and why?" })).toBeVisible();
    await page.screenshot({ path: "../.verification/real-dashboard-mobile.png", fullPage: true });
  }
  expect(errors).toEqual([]);
});

test("real-model demo action → new analysis → scoped dashboard", async ({ page }) => {
  test.skip(process.env.E2E_REAL_NLP !== "1", "Opt in with the production servers and real weights running.");
  await page.goto("/datasets");
  await page.getByRole("button", { name: "Use Demo Dataset", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Imported posts preview" })).toBeVisible();
  await expect(page.getByText(/900 source rows/)).toBeVisible();
  const completedBefore = await page.getByRole("link", { name: "Open Dashboard", exact: true }).count();
  await page.getByRole("button", { name: "Run Analysis", exact: true }).click();
  await expect(page.getByRole("link", { name: "Open Dashboard", exact: true })).toHaveCount(completedBefore + 1, { timeout: 90000 });
  await page.getByRole("link", { name: "Open Dashboard", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Ranked trends" })).toBeVisible();
  await expect(page).toHaveURL(/dataset=.+&run=.+/);
  await page.screenshot({ path: "../.verification/real-demo-dashboard.png", fullPage: true });
  console.log(`Real demo context: ${page.url()}`);
});
