import { useWorkspace } from "./workspace";
import { format } from "@/lib/format";
export function ResultSummary() {
  const w = useWorkspace();
  const r = w.comparison?.[w.selected];
  const rows = r
    ? [
        ["Fulfilled / day", format(r.capacity.fulfilled_orders_per_day)],
        ["Monthly revenue", format(r.economics.total_revenue, "money")],
        [
          "Contribution margin",
          format(r.economics.contribution_margin, "percent"),
        ],
        [
          "Contribution / order",
          format(r.economics.contribution_per_order, "unitmoney"),
        ],
        [
          "Operating result / month",
          format(r.economics.operating_profit, "money"),
        ],
        [
          "Break-even demand / day",
          format(r.break_even.requested_orders_per_day),
        ],
        [
          "System utilisation",
          format(r.capacity.system_utilisation, "percent"),
        ],
        [
          "Active bottleneck",
          r.capacity.active_bottlenecks.join(" + ") || "None",
        ],
        [
          "Cash runway",
          r.cash.runway_status === "no_operating_burn"
            ? "No operating burn"
            : format(r.cash.static_runway_months, "months"),
        ],
      ]
    : [];
  return (
    <section className="sticky-results" aria-label="Editing result summary">
      <div className="summary-header">
        <div>
          <span className="eyebrow">
            {w.selected.toUpperCase()} ·{" "}
            {r ? "CURRENT CALCULATION" : "RECALCULATION REQUIRED"}
          </span>
          <strong>{w.drafts?.[w.selected].name}</strong>
        </div>
        <button
          className="primary"
          type="submit"
          form="scenario-form"
          disabled={w.busy}
        >
          {w.busy ? "Working…" : "Calculate both"}
        </button>
      </div>
      {r ? (
        <dl className="summary-values">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p role="status" className="summary-pending">
          Assumptions changed. Calculate both scenarios to see current results;
          no previous values are presented as current.
        </p>
      )}
    </section>
  );
}
