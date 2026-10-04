import { sameAssumption } from "./fields";
import type { Comparison, Draft } from "@/types/model";
import { format, signed, type Format } from "@/lib/format";
const metrics: [string, string, Format, "higher" | "lower" | "neutral"][] = [
  ["total_revenue", "Monthly revenue", "money", "neutral"],
  ["contribution_margin", "Contribution margin", "percent", "higher"],
  ["operating_profit", "Monthly operating result", "money", "higher"],
  ["cost_per_order", "Total cost per fulfilled order", "unitmoney", "lower"],
  ["fulfilled_orders_per_day", "Fulfilled orders / day", "number", "neutral"],
  [
    "break_even_requested_orders_per_day",
    "Break-even demand / day",
    "number",
    "lower",
  ],
  ["system_utilisation", "System capacity utilisation", "percent", "neutral"],
  [
    "required_fulfilment_workers",
    "Required fulfilment staff · FTE",
    "number",
    "neutral",
  ],
  ["required_riders", "Required riders · FTE", "number", "neutral"],
  ["static_runway_months", "Static cash runway", "months", "higher"],
];
export function ComparisonTable({
  comparison: c,
  drafts,
}: {
  comparison: Comparison;
  drafts: { baseline: Draft; alternative: Draft };
}) {
  const changed = Object.keys(drafts.baseline.assumptions).filter(
    (key) =>
      !sameAssumption(
        drafts.baseline.assumptions[key as keyof Draft["assumptions"]],
        drafts.alternative.assumptions[key as keyof Draft["assumptions"]],
      ),
  );
  return (
    <section className="panel comparison-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">BASELINE VS ALTERNATIVE</span>
          <h2>Decision comparison</h2>
        </div>
        <span className="badge">{changed.length} changed assumptions</span>
      </div>
      {!c.same_operating_days && (
        <div className="alert warning">
          Different operating months: {c.baseline_operating_days_per_month} vs{" "}
          {c.alternative_operating_days_per_month} trading days. Monthly fixed
          costs are not prorated.
        </div>
      )}
      <div className="table-scroll">
        <table className="comparison-table">
          <caption className="sr-only">
            Backend calculated baseline and alternative differences
          </caption>
          <thead>
            <tr>
              <th>Metric</th>
              <th>
                {drafts.baseline.name || "Baseline"}
                <small>Baseline</small>
              </th>
              <th>
                {drafts.alternative.name || "Alternative"}
                <small>Alternative</small>
              </th>
              <th>
                Change<small>Alternative − baseline</small>
              </th>
            </tr>
          </thead>
          <tbody>
            {metrics.map(([key, label, kind, direction]) => {
              const d = c.deltas[key];
              if (!d) return null;
              const delta =
                d.absolute_change === null ? 0 : Number(d.absolute_change);
              const tone =
                direction === "neutral" || delta === 0
                  ? ""
                  : (direction === "higher" ? delta > 0 : delta < 0)
                    ? "positive"
                    : "negative";
              const display = (slot: "baseline" | "alternative") =>
                key === "static_runway_months" &&
                c[slot].cash.runway_status === "no_operating_burn"
                  ? "No operating burn"
                  : format(d[slot], kind);
              return (
                <tr key={key}>
                  <th scope="row">{label}</th>
                  <td>{display("baseline")}</td>
                  <td>{display("alternative")}</td>
                  <td className={tone}>
                    {signed(
                      d.absolute_change,
                      kind === "percent" ? "points" : kind,
                    )}
                  </td>
                </tr>
              );
            })}
            <tr>
              <th scope="row">Current break-even position</th>
              <td>
                {c.baseline.economics.is_at_or_above_break_even
                  ? "At / above"
                  : "Below"}
              </td>
              <td>
                {c.alternative.economics.is_at_or_above_break_even
                  ? "At / above"
                  : "Below"}
              </td>
              <td>Operating result ≥ 0</td>
            </tr>
            <tr>
              <th scope="row">Break-even reachable at capacity</th>
              <td>
                {c.baseline.break_even.reachable_at_current_capacity
                  ? "Yes"
                  : "No"}
              </td>
              <td>
                {c.alternative.break_even.reachable_at_current_capacity
                  ? "Yes"
                  : "No"}
              </td>
              <td>At current staffing</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="table-note">
        Green indicates higher profit, margin or runway, or lower costs /
        break-even demand. Revenue, throughput, staffing and utilisation changes
        are neutral; more is not always better. Undefined ratios appear as —.
      </p>
    </section>
  );
}
