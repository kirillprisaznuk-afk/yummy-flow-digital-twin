import { test, expect } from "@playwright/test";
import {
  fields,
  sameAssumption,
  shiftDecimal,
} from "../features/scenarios/fields";
import { parseCsv, exportCsv } from "../features/scenarios/csv";
import type { Assumptions } from "../types/model";

const backend = process.env.TEST_BACKEND_URL || "http://127.0.0.1:8000";
test("all assumption controls cover the actual API contract with correct unit conversion", async ({
  page,
  request,
}) => {
  const defaults: Assumptions = await (
    await request.get(`${backend}/api/v1/defaults`)
  ).json();
  expect(fields.map((f) => f.key).sort()).toEqual(Object.keys(defaults).sort());
  expect(new Set(fields.map((f) => f.label)).size).toBe(fields.length);
  expect(sameAssumption("28.0", "28")).toBe(true);
  await page.goto("/scenarios");
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  for (const field of fields) {
    const control = page.getByLabel(field.label, { exact: true });
    await expect(control).toHaveValue(
      field.percent
        ? shiftDecimal(String(defaults[field.key]), 2)
        : String(defaults[field.key]),
    );
  }
  await page.getByRole("button", { name: "Alternative", exact: true }).click();
  await page.getByLabel("Product gross margin", { exact: true }).fill("40");
  const call = page.waitForRequest(
    (r) => r.url().endsWith("/api/backend/compare") && r.method() === "POST",
  );
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  const body = (await call).postDataJSON();
  expect(body.baseline).toEqual(defaults);
  expect(body.alternative.gross_margin).toBe("0.4");
  expect(body.alternative).toEqual({ ...defaults, gross_margin: "0.4" });
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Baseline", exact: true }).click();
  await expect(
    page.getByLabel("Product gross margin", { exact: true }),
  ).toHaveValue("25");
});

test("CSV round-trip and strict rejection of unsafe, ambiguous and incomplete files", async ({
  request,
}) => {
  const defaults = await (
    await request.get(`${backend}/api/v1/defaults`)
  ).json();
  const csv = exportCsv(defaults);
  expect(parseCsv("\ufeff" + csv)).toEqual(defaults);
  expect(() => parseCsv(csv.replace('"700"', '"=1+1"'))).toThrow(
    "plain number",
  );
  expect(() => parseCsv(csv.replace('"700"', '"-1"'))).toThrow();
  expect(() => parseCsv(csv.replace('"700"', '"1e3"'))).toThrow();
  expect(() => parseCsv(csv.replace('"700"', '"NaN"'))).toThrow();
  expect(() => parseCsv(csv.replace('"25"', '"101"'))).toThrow("range");
  expect(() => parseCsv(csv.replace('"25"', '"25.12345"'))).toThrow(
    "decimal places",
  );
  expect(() => parseCsv(csv.replace('"Orders per day"', '"Unknown"'))).toThrow(
    "Unknown assumption",
  );
  expect(() => parseCsv(csv.replace('"orders/day"', '"orders/month"'))).toThrow(
    "expected unit",
  );
  expect(() => parseCsv(csv + csv.split("\r\n")[1] + "\r\n")).toThrow(
    "Duplicate",
  );
  expect(() => parseCsv(csv.split("\r\n").slice(0, -3).join("\r\n"))).toThrow(
    "Missing",
  );
  expect(() => parseCsv(csv + '"unclosed')).toThrow("unclosed");
  expect(() => parseCsv("x".repeat(64001))).toThrow("64 KB");
});

test("distinct imported scenario propagates through every analysis view and persisted rename/delete", async ({
  page,
  request,
}) => {
  const defaults: Assumptions = await (
    await request.get(`${backend}/api/v1/defaults`)
  ).json();
  const alternative: Assumptions = {
    ...defaults,
    orders_per_day: "120",
    average_order_value: "40",
    gross_margin: "0.4",
    riders: 2,
    fulfilment_workers: 2,
    starting_cash: "5000",
  };
  const evaluated = await (
    await request.post(`${backend}/api/v1/evaluate`, { data: alternative })
  ).json();
  const money = (v: string) =>
    new Intl.NumberFormat("en-IE", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(Number(v));
  const name = `Decision workflow ${Date.now()}`;
  let id: string | undefined;
  try {
    await page.goto("/scenarios");
    await expect(
      page.getByRole("heading", { name: "Decision comparison" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Alternative", exact: true })
      .click();
    await page.getByLabel("Import assumptions file").setInputFiles({
      name: "assumptions.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(exportCsv(alternative)),
    });
    await expect(
      page.getByRole("status").filter({ hasText: "CSV validated" }),
    ).toBeVisible();
    await page.getByLabel("Scenario name", { exact: true }).fill(name);
    await page
      .getByRole("button", { name: "Calculate both", exact: true })
      .click();
    const summary = page.getByRole("region", {
      name: "Editing result summary",
    });
    await expect(summary).toContainText(
      money(evaluated.economics.operating_profit),
    );
    await expect(
      page.getByRole("row").filter({ hasText: "Monthly operating result" }),
    ).toContainText(money(evaluated.economics.operating_profit));
    await page
      .getByRole("button", { name: "Save as new", exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: "New scenario saved" }),
    ).toBeVisible();
    id = (
      await (await request.get(`${backend}/api/v1/scenarios?limit=100`)).json()
    ).find((r: { name: string }) => r.name === name).id;
    await page.reload();
    await expect(page.getByLabel("Scenario name", { exact: true })).toHaveValue(
      name,
    );
    await expect(
      page.getByLabel("Orders per day", { exact: true }),
    ).toHaveValue("120");
    await expect(
      page.getByRole("button", { name: "Alternative", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await page.getByRole("link", { name: "01 Overview" }).click();
    await expect(
      page
        .getByText(money(evaluated.economics.total_revenue), { exact: true })
        .first(),
    ).toBeVisible();
    await page
      .getByRole("link", { name: "03 Operations", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Active bottleneck: delivery" }),
    ).toBeVisible();
    await expect(
      page.getByRole("row").filter({ hasText: "Delivery riders" }),
    ).toContainText("100%");
    await page
      .getByRole("link", { name: /Unit Economics$/, exact: false })
      .click();
    await expect(
      page
        .getByRole("row")
        .filter({ hasText: "Product sales / average order value" }),
    ).toContainText("€40.00");
    await expect(
      page.getByRole("row").filter({ hasText: "Operating result" }),
    ).toContainText(money(evaluated.economics.operating_profit));
    await page.getByRole("link", { name: "02 Scenario Lab" }).click();
    await page
      .getByLabel("Scenario name", { exact: true })
      .fill(name + " renamed");
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: "Update saved", exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: "Saved scenario updated" }),
    ).toBeVisible();
    expect(
      (await (await request.get(`${backend}/api/v1/scenarios/${id}`)).json())
        .name,
    ).toBe(name + " renamed");
    page.once("dialog", (dialog) => dialog.dismiss());
    await page
      .getByRole("button", { name: `Delete ${name} renamed`, exact: true })
      .click();
    expect(
      (await request.get(`${backend}/api/v1/scenarios/${id}`)).status(),
    ).toBe(200);
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: `Delete ${name} renamed`, exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: "Scenario deleted" }),
    ).toBeVisible();
    expect(
      (await request.get(`${backend}/api/v1/scenarios/${id}`)).status(),
    ).toBe(404);
    id = undefined;
    await expect(
      page.getByRole("button", { name: "Update saved", exact: true }),
    ).toHaveCount(0);
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: "Reset to synthetic defaults" })
      .click();
    await expect(
      page.getByLabel("Orders per day", { exact: true }),
    ).toHaveValue("700");
  } finally {
    if (id) await request.delete(`${backend}/api/v1/scenarios/${id}`);
  }
});

test("invalid CSV is atomic and leaves both scenarios untouched", async ({
  page,
}) => {
  await page.goto("/scenarios");
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByLabel("Import assumptions file").setInputFiles({
    name: "bad.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("Assumption,Value,Unit\nOrders per day,900,orders/day"),
  });
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Missing assumptions",
  );
  await expect(page.getByLabel("Orders per day", { exact: true })).toHaveValue(
    "700",
  );
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
});

test("Operations and Unit Economics stay readable on desktop/mobile and at zero volume", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.goto("/operations");
  await expect(
    page.getByRole("heading", { name: "Capacity by resource" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/operations-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("link", { name: /Unit Economics$/, exact: false })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Monthly and per-order contribution bridge",
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/economics-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ["/operations", "/economics", "/scenarios"]) {
    await page.goto(path);
    await expect(
      page.getByRole("main").getByRole("heading", { level: 1 }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await page.getByLabel("Orders per day", { exact: true }).fill("0");
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: /Unit Economics$/, exact: false })
    .click();
  await expect(
    page
      .getByRole("row")
      .filter({ hasText: "Product sales / average order value" }),
  ).toContainText("—");
  await expect(
    page
      .getByRole("row")
      .filter({ hasText: "Fixed operating costs · includes all payroll" }),
  ).toContainText("€109,660");
});
