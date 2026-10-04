# Screenshot provenance and demo

These are real Chromium captures of the locally served application, taken on 2026-10-04 at a 1440 × 1100 viewport. The page pixels and financial values have not been edited. Overview, Operations and Unit Economics capture complete pages; Scenario Lab captures the viewport; Risk & Simulation captures its results region for readability. No browser chrome or development overlays are included.

All five show the same synthetic default baseline: 700 requested orders/day, €28 basket, 25% product gross margin and the remaining central defaults. Scenario Lab also has a demand-only alternative of 840/day. Both fulfil 652.8/day because delivery capacity binds. The saved demo name is presentation metadata, not a different set of assumptions.

[demo-results.json](demo-results.json) contains actual API outputs, all baseline assumptions, model/analytics versions, simulation settings, Python version and the sample digest. This deliberately retained synthetic result record makes README numbers independently traceable; it contains no saved UUIDs, credentials or personal information.

| File | View |
| --- | --- |
| [overview.png](overview.png) | Executive economics and demand/capacity picture |
| [scenario-lab.png](scenario-lab.png) | Baseline editor, sticky summary and demand alternative |
| [operations.png](operations.png) | Resource utilisation, gaps and required budgets |
| [unit-economics.png](unit-economics.png) | Monthly and per-fulfilled-order contribution bridge |
| [risk-simulation.png](risk-simulation.png) | Conditional outcome distribution and operational risk |

## Reproduce

Run the PostgreSQL-backed API and a locally served frontend production build, then from `frontend/`:

```sh
node scripts/capture-portfolio.mjs
```

Chromium must already be installed through Playwright. The script uses a fresh browser context, exercises edit/calculate/compare/save/reload/navigation/sensitivity/simulation, and removes only the scenario it creates. Existing saved scenarios remain untouched; inspect the Scenario Lab library for private names before publishing a new capture. The script overwrites these five screenshots and the synthetic result record.

The default 1,000 draws with seed 42 return expected monthly result €21,839, P10 €11,373, P50 €21,761 and P90 €32,198, rounded for display. Positive profit in 99.8% of draws is conditional on narrow illustrative ranges. It is not calibrated business risk. Product gross margin has the largest tested sensitivity range, and a 20% relative reduction moves the deterministic result into a loss. Defaults were preserved rather than tuned for attractive outcomes.
