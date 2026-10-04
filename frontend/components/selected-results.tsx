"use client";
import type { Draft, Evaluation } from "@/types/model";
import { useWorkspace } from "@/features/scenarios/workspace";
export function SelectedResults({
  title,
  children,
}: {
  title: string;
  children: (r: Evaluation, draft: Draft) => React.ReactNode;
}) {
  const w = useWorkspace();
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">SCENARIO DECISION SUPPORT</span>
          <h1>{title}</h1>
        </div>
      </div>
      {w.drafts && (
        <div className="scenario-context">
          <label htmlFor="analysis-scenario">Selected scenario</label>
          <select
            id="analysis-scenario"
            value={w.selected}
            onChange={(e) =>
              w.setSelected(e.target.value as "baseline" | "alternative")
            }
          >
            <option value="baseline">
              Baseline · {w.drafts.baseline.name}
            </option>
            <option value="alternative">
              Alternative · {w.drafts.alternative.name}
            </option>
          </select>
          <span className="badge">
            {w.drafts[w.selected].dirty
              ? "Unsaved edits"
              : w.drafts[w.selected].id
                ? "Saved scenario"
                : "Synthetic defaults"}
          </span>
        </div>
      )}
      {w.comparison && w.drafts ? (
        children(w.comparison[w.selected], w.drafts[w.selected])
      ) : (
        <div className="empty-state">
          <h2>
            {w.busy ? "Loading results…" : "Calculate current assumptions"}
          </h2>
          <p>
            All analysis pages use the same selected scenario. Edited inputs
            must be recalculated.
          </p>
          <button
            disabled={w.busy || !w.drafts}
            onClick={() => void w.calculate()}
          >
            Calculate scenarios
          </button>
        </div>
      )}
    </>
  );
}
