# Frontend — decision workspace

Next.js App Router, React, TypeScript and Tailwind CSS. All financial and operational outputs come from FastAPI; no business formulas are reimplemented here. Simple capacity bars and semantic financial/comparison tables avoid an unnecessary charting dependency.

## Run locally

Requires Node.js 22+ and pnpm 11.25.0. Start PostgreSQL and the backend first (see the root README). From `frontend/`:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

Open http://127.0.0.1:3000. The default server-only `BACKEND_URL` is http://127.0.0.1:8000. To change it, copy this directory's `.env.example` to `.env.local`. Do not copy the root database `.env` into the frontend and do not use `NEXT_PUBLIC_` for secrets. Neither server needs a paid service.

For a production build served locally:

```sh
pnpm build
pnpm start
```

## Validate

```sh
pnpm lint
pnpm typecheck
pnpm format:check
pnpm exec playwright install chromium
pnpm test
```

Browser tests require the running built frontend and the PostgreSQL-backed API. The real persistence test creates a uniquely named synthetic scenario, verifies save/replacement/reload and removes only that UUID. Other tests deliberately simulate unavailable services and validation failures. Screenshots and traces go to ignored `test-results/`.

ESLint 9.39.5 is retained because Next's current React/import/accessibility plugins do not support ESLint 10. The registry marks ESLint 9 deprecated; upgrade together with compatible plugins. Dependency peer checks and the production audit currently pass. The native `unrs-resolver` installation script is explicitly allowed for lint resolution; other dependency build scripts are not broadly enabled.

## API contract

From the repository root, regenerate the contract after intentional API changes:

```sh
python scripts/export_api.py
cd frontend
pnpm api:types
pnpm typecheck
```

Use the backend virtual environment for the Python command. `api/openapi.json` is an exported contract; `types/schema.ts` is generated. Neither requires a database connection to regenerate.

`api/client.ts` centralises browser requests. `app/api/backend/[...path]/route.ts` only forwards known model/scenario paths to the configured server, rejects cross-origin writes and translates unavailable upstream responses. It forwards no browser cookies or database credentials. This is a local single-user interface, not an authenticated multi-user application.

## State and limitations

Baseline and alternative drafts live in a shared React provider and survive in-app navigation. Every numeric edit invalidates both evaluations until recalculated. Saving persists assumptions, not cached results. Loading uses the saved-evaluation endpoint, so incompatible historical model versions produce a useful error rather than silent recalculation; explicit migration/copying of old versions remains an API workflow.

Save as new creates a record. Rename in the editor and explicitly confirm Update saved to replace it. Delete also requires confirmation; open assumptions remain as unsaved drafts. Loading, importing or resetting a dirty slot prompts before discarding edits. The library supports pagination.

Saved slot UUIDs and selection are remembered in browser local storage and reloaded from the API after refresh. Unsaved edits do not survive a full reload; a before-unload warning is provided. Unavailable saved records show a warning and synthetic defaults. There is no authentication or cross-tab conflict resolution.

Scenario Lab has a sticky result summary and explicit recalculation after numeric changes. Operations explains resource utilisation, eligible-demand shortfalls and required FTE budgets. Unit Economics shows a monthly/per-order contribution bridge using backend allocations. Zero-volume allocations are undefined, not zero. Risk & Simulation implements backend sensitivity and bounded seeded Monte Carlo; forecasting is outside the final scope.

## Assumptions CSV

Export the selected draft to get a complete template. The exact header is `Assumption,Value,Unit`; labels and units must match the exported file. Percentages use `25` for 25%, decimal separators are dots, monetary inputs are VAT-exclusive EUR, and every assumption must appear once. UTF-8 BOM, CRLF/LF and quoted CSV cells are supported. Files are limited to 64 KB. Unknown/duplicate/missing fields, wrong units, formulas, scientific notation and out-of-range values are rejected. The backend also validates before any draft changes.

Import produces an unsaved synthetic draft without a saved UUID. Calculate to compare, then save explicitly. Export contains assumptions only, not scenario names, financial results or historical data. For a synthetic-default template, reset a slot before exporting.


## Risk workspace

Run sensitivity or simulation explicitly for the selected scenario. Numeric scenario edits require normal workspace recalculation first. Risk results are hidden when selection, assumptions or relevant settings change; late responses retain their original input key. Uncertainty settings and results are page-local and are not saved with scenarios. The deterministic summary is visually distinct from simulated outcomes.

Uncertainty defaults come from the API, not frontend constants. The UI offers 1,000/5,000/10,000 draws and an optional seed. The backend computes all ranks, distributions, bins, percentiles and probabilities. Chart code only scales supplied data; detailed tables provide accessible equivalents. On narrow screens the histogram scrolls horizontally rather than shrinking labels. Competing simulations return a retryable 429; leaving a page does not cancel backend work. See the Methodology page for conditional-probability and independence limitations.
