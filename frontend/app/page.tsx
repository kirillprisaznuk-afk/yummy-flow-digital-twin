"use client";
import Link from "next/link";
import { useWorkspace } from "@/features/scenarios/workspace";
import { Results } from "@/features/overview/results";
export default function Overview() {
  const w = useWorkspace();
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">EXECUTIVE OPERATING SUMMARY</span>
          <h1>Overview</h1>
          <p>
            Understand the economics. Find the constraint. Test the decision.
          </p>
        </div>
        <Link className="button primary" href="/scenarios">
          Open Scenario Lab <span aria-hidden="true">↗</span>
        </Link>
      </div>
      {!w.drafts ? (
        <div className="empty-state" role="status">
          <h2>
            {w.busy
              ? "Loading the operating model…"
              : "The model is unavailable"}
          </h2>
          <p>
            {w.busy
              ? "Retrieving synthetic assumptions and calculating the baseline."
              : "Use Retry connection above to reconnect."}
          </p>
        </div>
      ) : (
        <>
          <div className="scenario-context">
            <div>
              <span className="eyebrow">SELECTED SCENARIO</span>
              <label className="sr-only" htmlFor="overview-scenario">
                Selected scenario
              </label>
              <select
                id="overview-scenario"
                value={w.selected}
                onChange={(e) =>
                  w.setSelected(e.target.value as "baseline" | "alternative")
                }
              >
                <option value="baseline">
                  {w.drafts.baseline.name || "Baseline"}
                </option>
                <option value="alternative">
                  {w.drafts.alternative.name || "Alternative"}
                </option>
              </select>
            </div>
            <span>
              {w.drafts[w.selected].assumptions.operating_days_per_month}{" "}
              operating days / month
            </span>
            <span className="badge">
              {w.drafts[w.selected].dirty
                ? "Unsaved edits"
                : w.drafts[w.selected].id
                  ? "Saved scenario"
                  : "Synthetic default"}
            </span>
          </div>
          {w.comparison ? (
            <Results result={w.comparison[w.selected]} />
          ) : (
            <div className="empty-state">
              <span className="eyebrow">ASSUMPTIONS CHANGED</span>
              <h2>Calculate to refresh this summary</h2>
              <p>
                Previous results are hidden so they cannot be mistaken for the
                current assumptions.
              </p>
              <button
                className="primary"
                disabled={w.busy}
                onClick={() => void w.calculate()}
              >
                {w.busy ? "Calculating…" : "Calculate scenarios"}
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
