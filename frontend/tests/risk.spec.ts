import { sameAssumption } from "../features/scenarios/fields";
import { test, expect } from "@playwright/test";

test("risk uses the selected scenario, validates settings, reproduces seeds and invalidates stale results", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/risk");
  await expect(
    page.getByRole("button", { name: "Run sensitivity", exact: true }),
  ).toBeEnabled();
  const sensitivityResponse = page.waitForResponse((r) =>
    r.url().endsWith("analytics/sensitivity"),
  );
  await page
    .getByRole("button", { name: "Run sensitivity", exact: true })
    .click();
  const sensitivity = await (await sensitivityResponse).json();
  await expect(
    page.getByRole("region", { name: "Sensitivity analysis", exact: true }),
  ).toContainText(sensitivity.variables[0].label);
  async function run() {
    const response = page.waitForResponse((r) =>
      r.url().endsWith("analytics/simulation"),
    );
    await page
      .getByRole("button", { name: "Run simulation", exact: true })
      .click();
    const result = await (await response).json();
    await expect(
      page.getByRole("region", { name: "Simulation results", exact: true }),
    ).toBeVisible();
    return result;
  }
  const first = await run();
  const repeated = await run();
  expect(repeated).toEqual(first);
  await page.getByLabel("Random seed (optional)").fill("43");
  await expect(
    page.getByRole("region", { name: "Simulation results", exact: true }),
  ).toHaveCount(0);
  const otherSeed = await run();
  expect(otherSeed.sample_digest).not.toBe(first.sample_digest);
  await page
    .getByLabel("Requested orders uncertainty", { exact: true })
    .fill("30");
  const wider = await run();
  expect(wider.histogram).not.toEqual(otherSeed.histogram);
  await page
    .getByLabel("Requested orders uncertainty", { exact: true })
    .fill("-1");
  await page
    .getByRole("button", { name: "Run simulation", exact: true })
    .click();
  expect(
    await page
      .getByLabel("Requested orders uncertainty", { exact: true })
      .evaluate((e: HTMLInputElement) => e.validity.valid),
  ).toBe(false);
  await page
    .getByRole("button", { name: "Set zero uncertainty", exact: true })
    .click();
  const zero = await run();
  expect(
    sameAssumption(zero.p10, zero.baseline.economics.operating_profit),
  ).toBe(true);
  expect(sameAssumption(zero.expected_operating_profit, zero.p50)).toBe(true);
  expect(zero.histogram).toHaveLength(1);
  await page
    .getByLabel("Selected scenario", { exact: true })
    .selectOption("alternative");
  await expect(
    page.getByRole("region", { name: "Simulation results", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: /Scenario Lab$/ }).click();
  await page.getByLabel("Orders per day", { exact: true }).fill("120");
  await page.getByLabel("Average order value", { exact: true }).fill("40");
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Risk & Simulation$/ }).click();
  await expect(
    page.getByRole("button", { name: "Run simulation", exact: true }),
  ).toBeEnabled();
  const alternative = await run();
  expect(alternative.baseline.economics.total_revenue).not.toBe(
    first.baseline.economics.total_revenue,
  );
  const changedResponse = page.waitForResponse((r) =>
    r.url().endsWith("analytics/sensitivity"),
  );
  await page
    .getByRole("button", { name: "Run sensitivity", exact: true })
    .click();
  const changed = await (await changedResponse).json();
  expect(changed.baseline).toEqual(alternative.baseline);
  expect(changed.baseline.economics.operating_profit).not.toBe(
    sensitivity.baseline.economics.operating_profit,
  );
  await expect(page.getByRole("main")).not.toContainText(
    /NaN|Infinity|undefined/,
  );
  expect(errors).toEqual([]);
});

test("simulation failure preserves settings and can be retried", async ({
  page,
}) => {
  await page.goto("/risk");
  await expect(
    page.getByRole("button", { name: "Run simulation", exact: true }),
  ).toBeEnabled();
  await page.route("**/api/backend/analytics/simulation", (route) =>
    route.fulfill({
      status: 429,
      json: {
        detail:
          "A simulation is already running. Please retry when it finishes.",
      },
    }),
  );
  await page
    .getByRole("button", { name: "Run simulation", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "already running",
  );
  await expect(page.getByLabel("Random seed (optional)")).toHaveValue("42");
  await page.unroute("**/api/backend/analytics/simulation");
  await page
    .getByRole("button", { name: "Run simulation", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Simulation results", exact: true }),
  ).toBeVisible();
});

test("risk charts have readable desktop and mobile layouts", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.goto("/risk");
  await expect(
    page.getByRole("button", { name: "Run sensitivity", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Run sensitivity", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run simulation", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Run simulation", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Simulation results", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/risk-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/risk-mobile.png",
    fullPage: true,
  });
});
