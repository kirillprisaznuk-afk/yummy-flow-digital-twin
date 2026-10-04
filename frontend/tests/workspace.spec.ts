import { test, expect } from "@playwright/test";
import { shiftDecimal } from "../features/scenarios/fields";

test("percentage editing preserves the backend decimal precision", () => {
  expect(shiftDecimal("0.851234", 2)).toBe("85.1234");
  expect(shiftDecimal("85.1234", -2)).toBe("0.851234");
  expect(shiftDecimal("0.0001", -2)).toBe("0.000001");
  expect(shiftDecimal("100", -2)).toBe("1");
  expect(shiftDecimal("", -2)).toBe("");
});

test("live API calculation, comparison, save, replacement and reload", async ({
  page,
  request,
}) => {
  const ids: string[] = [];
  const name = `Browser verification ${Date.now()}`;
  const backend = process.env.TEST_BACKEND_URL || "http://127.0.0.1:8000";
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    await page.goto("/scenarios");
    await expect(
      page.getByRole("heading", { name: "Decision comparison" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Alternative", exact: true })
      .click();
    await page.getByLabel("Scenario name", { exact: true }).fill(name);
    await page.getByLabel("Average order value", { exact: true }).fill("32");
    await expect(
      page.getByRole("heading", { name: "Comparison awaits calculation" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Calculate scenarios", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Decision comparison" }),
    ).toBeVisible();
    const defaults = await (
      await request.get(`${backend}/api/v1/defaults`)
    ).json();
    const expected = await (
      await request.post(`${backend}/api/v1/compare`, {
        data: {
          baseline: defaults,
          alternative: { ...defaults, average_order_value: "32" },
        },
      })
    ).json();
    const euro = new Intl.NumberFormat("en-IE", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    });
    const resultRow = page
      .getByRole("row")
      .filter({ hasText: "Monthly operating result" });
    await expect(resultRow).toContainText(
      euro.format(Number(expected.alternative.economics.operating_profit)),
    );
    await page
      .getByRole("button", { name: "Save as new", exact: true })
      .click();
    await expect(page.getByRole("status")).toHaveText("New scenario saved.");
    const records = await (
      await request.get(`${backend}/api/v1/scenarios?limit=100`)
    ).json();
    const saved = records.find(
      (record: { name: string }) => record.name === name,
    );
    expect(saved).toBeTruthy();
    ids.push(saved.id);
    await page.getByLabel("Average order value", { exact: true }).fill("33");
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: "Update saved", exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: "Saved scenario updated" }),
    ).toHaveText("Saved scenario updated.");
    expect(
      (
        await (
          await request.get(`${backend}/api/v1/scenarios/${saved.id}`)
        ).json()
      ).assumptions.average_order_value,
    ).toBe("33");
    await page.reload();
    await page.getByRole("button", { name: new RegExp("^" + name) }).click();
    await expect(
      page.getByLabel("Average order value", { exact: true }),
    ).toHaveValue("33");
    await page
      .getByRole("button", { name: "Calculate scenarios", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Decision comparison" }),
    ).toBeVisible();
    await page.getByRole("link", { name: "01 Overview" }).click();
    await expect(page.getByLabel("Selected scenario")).toContainText(name);
    expect(errors).toEqual([]);
  } finally {
    for (const id of ids)
      await request.delete(`${backend}/api/v1/scenarios/${id}`);
  }
});

test("zero demand, validation, and no stale results after edits", async ({
  page,
}) => {
  await page.goto("/scenarios");
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  const orders = page.getByLabel("Orders per day", { exact: true });
  await orders.fill("-1");
  await page
    .getByRole("button", { name: "Calculate scenarios", exact: true })
    .click();
  expect(
    await orders.evaluate((input: HTMLInputElement) => input.validity.valid),
  ).toBe(false);
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toHaveCount(0);
  await orders.fill("0");
  await page
    .getByRole("button", { name: "Calculate scenarios", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "01 Overview" }).click();
  await expect(
    page.getByText("Below break-even", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("€0", { exact: true }).first()).toBeVisible();
});

test("connection failure is recoverable and storage failure preserves calculations", async ({
  page,
}) => {
  await page.route("**/api/backend/defaults", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "Modelling service unavailable" },
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Modelling service unavailable",
  );
  await page.unroute("**/api/backend/defaults");
  await page.route("**/api/backend/scenarios?*", (route) =>
    route.fulfill({ status: 503, json: { detail: "Storage unavailable" } }),
  );
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(
    page.getByRole("heading", { name: "Demand meets capacity" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "02 Scenario Lab" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Saved scenarios could not be loaded",
  );
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
});

test("desktop and mobile layouts, risk navigation, and screenshots", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Demand meets capacity" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/overview-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "02 Scenario Lab" }).click();
  await page.screenshot({
    path: "test-results/scenarios-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "05 Risk & Simulation" }).click();
  await expect(
    page.getByRole("heading", { name: "Monte Carlo simulation", exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Demand meets capacity" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/overview-mobile.png",
    fullPage: true,
  });
});

test("server forwarding rejects unknown paths and cross-origin writes", async ({
  request,
}) => {
  expect((await request.get("/api/backend/not-a-real-endpoint")).status()).toBe(
    404,
  );
  expect(
    (
      await request.post("/api/backend/scenarios", {
        headers: { Origin: "https://other.example" },
        data: {},
      })
    ).status(),
  ).toBe(403);
});

test("failed calculation keeps edits and translates validation labels", async ({
  page,
}) => {
  await page.goto("/scenarios");
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByLabel("Average order value", { exact: true }).fill("31");
  await page.route("**/api/backend/compare", (route) =>
    route.fulfill({
      status: 422,
      json: {
        detail: [
          {
            loc: ["body", "baseline", "average_order_value"],
            msg: "Review this assumption",
            type: "value_error",
          },
        ],
      },
    }),
  );
  await page
    .getByRole("button", { name: "Run comparison", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Baseline · Average order value",
  );
  await expect(
    page.getByLabel("Average order value", { exact: true }),
  ).toHaveValue("31");
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toHaveCount(0);
  await page.unroute("**/api/backend/compare");
  await page
    .getByRole("button", { name: "Run comparison", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
