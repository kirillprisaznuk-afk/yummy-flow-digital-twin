// Capture the real local application using the documented synthetic defaults.
// Requires the API and a locally served production build on their default ports.
import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const output = fileURLToPath(
  new URL("../../docs/screenshots/", import.meta.url),
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const origin = "http://127.0.0.1:3000";
const api = "http://127.0.0.1:8000/api/v1";
let savedId;
try {
  await page.goto(`${origin}/scenarios`);
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByLabel("Orders per day", { exact: true }).fill("650");
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByLabel("Orders per day", { exact: true }).fill("700");
  await page
    .getByLabel("Scenario name", { exact: true })
    .fill("Portfolio demo · Madrid baseline");
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  const saveResponse = page.waitForResponse(
    (r) => r.url().endsWith("/scenarios") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save as new", exact: true }).click();
  savedId = (await (await saveResponse).json()).id;
  await expect(page.getByRole("status")).toHaveText("New scenario saved.");
  await page.reload();
  await expect(page.getByLabel("Orders per day", { exact: true })).toHaveValue(
    "700",
  );
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Alternative", exact: true }).click();
  await page.getByLabel("Orders per day", { exact: true }).fill("840");
  await page
    .getByRole("button", { name: "Calculate both", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Decision comparison" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Baseline", exact: true }).click();
  const defaults = await (await page.request.get(`${api}/defaults`)).json();
  const evaluation = await (
    await page.request.post(`${api}/evaluate`, { data: defaults })
  ).json();
  const comparison = await (
    await page.request.post(`${api}/compare`, {
      data: {
        baseline: defaults,
        alternative: { ...defaults, orders_per_day: "840" },
      },
    })
  ).json();
  expect(Number(comparison.deltas.total_revenue.absolute_change)).toBe(0);
  for (const [label, filename, heading] of [
    ["Overview", "overview", "Demand meets capacity"],
    ["Scenario Lab", "scenario-lab", "Decision comparison"],
    ["Operations", "operations", "Capacity by resource"],
    [
      "Unit Economics",
      "unit-economics",
      "Monthly and per-order contribution bridge",
    ],
  ]) {
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("link", { name: new RegExp(`${label}$`) })
      .click();
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: `${output}/${filename}.png`,
      fullPage: filename !== "scenario-lab",
    });
  }
  await page
    .getByRole("navigation", { name: "Primary navigation" })
    .getByRole("link", { name: /Risk & Simulation$/ })
    .click();
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
  const simulationResponse = page.waitForResponse((r) =>
    r.url().endsWith("analytics/simulation"),
  );
  await page
    .getByRole("button", { name: "Run simulation", exact: true })
    .click();
  const simulation = await (await simulationResponse).json();
  await expect(
    page.getByRole("region", { name: "Simulation results", exact: true }),
  ).toBeVisible();
  expect(simulation.baseline).toEqual(evaluation);
  expect(sensitivity.baseline).toEqual(evaluation);
  await page
    .getByRole("region", { name: "Simulation results", exact: true })
    .screenshot({ path: `${output}/risk-simulation.png` });
  await page
    .getByRole("navigation", { name: "Primary navigation" })
    .getByRole("link", { name: /Methodology$/ })
    .click();
  await expect(
    page.getByRole("heading", { name: "Sales follow fulfilled demand" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
  await writeFile(
    `${output}/demo-results.json`,
    JSON.stringify(
      {
        classification: "illustrative_synthetic",
        assumptions: defaults,
        evaluation,
        alternative: {
          orders_per_day: "840",
          revenue_delta: comparison.deltas.total_revenue.absolute_change,
        },
        sensitivity_leader: sensitivity.variables[0].label,
        simulation: Object.fromEntries(
          [
            "model_version",
            "analytics_version",
            "python_version",
            "runs",
            "seed",
            "settings",
            "sample_digest",
            "expected_operating_profit",
            "p10",
            "p50",
            "p90",
            "probability_profit",
            "probability_capacity_constraint",
          ].map((key) => [key, simulation[key]]),
        ),
      },
      null,
      2,
    ) + "\n",
  );
  console.log(
    "PASS: complete portfolio workflow; five genuine screenshots and synthetic result record captured.",
  );
} finally {
  if (savedId) await page.request.delete(`${api}/scenarios/${savedId}`);
  await browser.close();
}
