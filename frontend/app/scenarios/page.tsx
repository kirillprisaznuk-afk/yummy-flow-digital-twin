"use client";
import { useWorkspace } from "@/features/scenarios/workspace";
import { ScenarioEditor } from "@/features/scenarios/editor";
import { ComparisonTable } from "@/features/scenarios/comparison";
import { ResultSummary } from "@/features/scenarios/result-summary";
import { CsvControls } from "@/features/scenarios/csv-controls";
import { fields, sameAssumption } from "@/features/scenarios/fields";
import { format } from "@/lib/format";
export default function Scenarios() {
  const w = useWorkspace();
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">ASSUMPTIONS → OUTCOMES</span>
          <h1>Scenario Lab</h1>
          <p>
            Change one decision at a time. Compare its financial and operational
            effects.
          </p>
        </div>
        <button
          className="primary"
          type="submit"
          form="scenario-form"
          disabled={w.busy || !w.drafts}
        >
          Run comparison
        </button>
      </div>
      {!w.drafts ? (
        <div className="empty-state" role="status">
          {w.busy
            ? "Loading scenario workspace…"
            : "Reconnect to open the workspace."}
        </div>
      ) : (
        <>
          <ResultSummary />
          <div className="lab-layout">
            <div>
              <ScenarioEditor />
              <CsvControls />
            </div>
            <aside className="lab-aside">
              <section className="panel">
                <div className="panel-heading">
                  <h2>Scenario library</h2>
                  <button
                    disabled={w.busy || w.libraryBusy}
                    onClick={() => void w.refreshSaved()}
                  >
                    Refresh
                  </button>
                </div>
                <p className="table-note">
                  Load into the selected {w.selected} slot.
                </p>
                {w.storageError && (
                  <p role="alert" className="alert warning">
                    {w.storageError}
                  </p>
                )}
                {w.libraryBusy && (
                  <p className="table-note">Loading saved scenarios…</p>
                )}
                {!w.saved.length && !w.storageError && !w.libraryBusy && (
                  <p className="empty-library">
                    No saved scenarios yet. Name your assumptions and choose
                    “Save as new”.
                  </p>
                )}
                <ul className="library">
                  {w.saved.map((scenario) => (
                    <li key={scenario.id}>
                      <button
                        disabled={w.busy || w.libraryBusy}
                        onClick={() => void w.load(w.selected, scenario.id)}
                      >
                        <strong>{scenario.name}</strong>
                        <span>
                          {format(scenario.assumptions.orders_per_day)}{" "}
                          orders/day ·{" "}
                          {format(
                            scenario.assumptions.average_order_value,
                            "money",
                          )}{" "}
                          basket
                        </span>
                      </button>
                      <button
                        className="danger-button"
                        aria-label={`Delete ${scenario.name}`}
                        disabled={w.busy}
                        onClick={() => void w.remove(scenario)}
                      >
                        Delete
                      </button>
                    </li>
                  ))}
                </ul>
                {w.hasMore && (
                  <button
                    disabled={w.busy || w.libraryBusy}
                    onClick={() => void w.refreshSaved(w.saved.length)}
                  >
                    Load more scenarios
                  </button>
                )}
              </section>
              <section className="panel">
                <div className="panel-heading">
                  <h2>What changed?</h2>
                </div>
                <p className="table-note">Alternative against baseline</p>
                <ul className="changes">
                  {fields
                    .filter(
                      (f) =>
                        !sameAssumption(
                          w.drafts!.baseline.assumptions[f.key],
                          w.drafts!.alternative.assumptions[f.key],
                        ),
                    )
                    .map((field) => (
                      <li key={field.key}>
                        <span>{field.label}</span>
                        <strong>
                          {format(
                            w.drafts!.baseline.assumptions[field.key],
                            field.percent ? "percent" : "number",
                          )}{" "}
                          →{" "}
                          {format(
                            w.drafts!.alternative.assumptions[field.key],
                            field.percent ? "percent" : "number",
                          )}{" "}
                          <small>{field.percent ? "" : field.unit}</small>
                        </strong>
                      </li>
                    ))}
                </ul>
                {fields.every((f) =>
                  sameAssumption(
                    w.drafts!.baseline.assumptions[f.key],
                    w.drafts!.alternative.assumptions[f.key],
                  ),
                ) && (
                  <p className="empty-library">
                    Both scenarios have the same assumptions. Edit the
                    alternative to test a decision.
                  </p>
                )}
              </section>
              <div className="model-note">
                <strong>Keep the comparison interpretable</strong>
                <p>
                  More demand does not automatically add staff. Capacity can cap
                  revenue while additional payroll remains a fixed monthly cost.
                </p>
                <p>All inputs are illustrative synthetic assumptions.</p>
              </div>
            </aside>
          </div>
          {w.comparison ? (
            <ComparisonTable comparison={w.comparison} drafts={w.drafts} />
          ) : (
            <section className="empty-state">
              <h2>Comparison awaits calculation</h2>
              <p>
                Review your edits, then calculate both scenarios. No stale
                results are shown.
              </p>
            </section>
          )}
        </>
      )}
    </>
  );
}
