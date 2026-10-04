import type { Evaluation } from "@/types/model";
import { format } from "@/lib/format";

const reasons: Record<Evaluation["break_even"]["reason"], string> = {
  reachable: "Break-even is within current system capacity.",
  capacity_shortfall:
    "Current capacity cannot serve enough orders to reach break-even. Investigate capacity and the resulting staffing cost together.",
  all_demand_stocked_out:
    "All demand is lost to stockouts. No requested-volume threshold can be reached.",
  nonpositive_contribution:
    "Contribution per order is nonpositive. More volume alone cannot cover fixed costs.",
  zero_fixed_costs:
    "Zero activity already breaks even because fixed costs are zero. This does not establish volume-led viability.",
};
export function Results({ result }: { result: Evaluation }) {
  const { capacity: c, economics: e, cash, break_even: be } = result;
  const capacityRows = [
    ["Requested demand", c.requested_orders_per_day, "demand"],
    ["Fulfilment staff", c.fulfilment_capacity_per_day, "fulfilment"],
    ["Delivery riders", c.delivery_capacity_per_day, "delivery"],
    ["Store throughput", c.store_capacity_per_day, "store"],
    ["System capacity", c.system_capacity_per_day, "system"],
  ];
  const scale = Math.max(1, ...capacityRows.map(([, value]) => Number(value)));
  const financialRows: [string, string, boolean?][] = [
    ["Product sales", e.product_revenue],
    ["Delivery fees", e.delivery_revenue],
    ["Total revenue", e.total_revenue, true],
    ["Product cost of goods", e.product_cogs],
    ["Shrinkage / wastage", e.shrinkage_cost],
    ["Packaging & consumables", e.variable_fulfilment_cost],
    ["Incremental delivery", e.variable_delivery_cost],
    ["Payment processing", e.payment_cost],
    ["Customer acquisition", e.acquisition_cost],
    ["Contribution", e.contribution, true],
    ["Fixed operating costs · includes payroll", e.fixed_operating_costs],
    ["Operating result", e.operating_profit, true],
  ];
  return (
    <>
      <div className="kpi-strip">
        <div>
          <span className="eyebrow">MONTHLY REVENUE</span>
          <strong>{format(e.total_revenue, "money")}</strong>
          <small>Product sales + delivery fees</small>
        </div>
        <div>
          <span className="eyebrow">CONTRIBUTION MARGIN</span>
          <strong>{format(e.contribution_margin, "percent")}</strong>
          <small>{format(e.contribution, "money")} before fixed costs</small>
        </div>
        <div>
          <span className="eyebrow">MONTHLY OPERATING RESULT</span>
          <strong
            className={e.is_at_or_above_break_even ? "positive" : "negative"}
          >
            {format(e.operating_profit, "money")}
          </strong>
          <small>EBITDA-style operating proxy</small>
        </div>
        <div>
          <span className="eyebrow">STATIC CASH RUNWAY</span>
          <strong>
            {cash.runway_status === "no_operating_burn"
              ? "No burn"
              : format(cash.static_runway_months, "months")}
          </strong>
          <small>
            {cash.cash_balance_is_zero
              ? "Starting cash is zero"
              : "Excludes working capital & investment"}
          </small>
        </div>
      </div>
      <div className="decision-band">
        <span
          className={`badge ${e.is_at_or_above_break_even ? "good" : "warn"}`}
        >
          {e.is_at_or_above_break_even
            ? "At or above break-even"
            : "Below break-even"}
        </span>
        <p>{reasons[be.reason]}</p>
      </div>
      <div className="results-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">OPERATING CONSTRAINTS</span>
              <h2>Demand meets capacity</h2>
            </div>
            <span className="unit-label">orders / day</span>
          </div>
          <div className="capacity-summary">
            <div>
              <strong>{format(c.fulfilled_orders_per_day)}</strong>
              <span>fulfilled / day</span>
            </div>
            <div>
              <strong>{format(c.system_utilisation, "percent")}</strong>
              <span>system utilisation</span>
            </div>
          </div>
          <div className="capacity-bars">
            {capacityRows.map(([label, value, resource]) => (
              <div key={label} className="capacity-row">
                <div>
                  <span>
                    {label}
                    {c.limiting_resources.includes(resource as "delivery") && (
                      <span className="limit-label">Limiting</span>
                    )}
                  </span>
                  <strong>{format(value)}</strong>
                </div>
                <div className="track" aria-hidden="true">
                  <div
                    className={
                      resource === "system"
                        ? "system-bar"
                        : resource === "demand"
                          ? "demand-bar"
                          : "resource-bar"
                    }
                    style={{ width: `${(Number(value) / scale) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="model-note">
            <strong>
              {c.active_bottlenecks.length
                ? "Demand is capacity constrained"
                : "No active capacity shortfall"}
            </strong>
            <p>{c.explanation}</p>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Orders lost to stockouts / day</dt>
              <dd>{format(c.stockout_lost_orders_per_day)}</dd>
            </div>
            <div>
              <dt>Orders lost to capacity / day</dt>
              <dd>{format(c.capacity_lost_orders_per_day)}</dd>
            </div>
            <div>
              <dt>Fulfilment staff needed for eligible demand</dt>
              <dd>{c.required_fulfilment_workers} FTE</dd>
            </div>
            <div>
              <dt>Riders needed for eligible demand</dt>
              <dd>{c.required_riders} FTE</dd>
            </div>
          </dl>
        </section>
        <section className="panel financial-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">MONTHLY ECONOMICS</span>
              <h2>From revenue to result</h2>
            </div>
            <span className="unit-label">EUR / month</span>
          </div>
          <table className="financial-table">
            <caption className="sr-only">
              Monthly operating statement. Costs are shown as positive expenses.
            </caption>
            <thead>
              <tr>
                <th scope="col">Operating statement</th>
                <th scope="col">Amount</th>
              </tr>
            </thead>
            <tbody>
              {financialRows.map(([label, value, total]) => (
                <tr key={label} className={total ? "subtotal" : ""}>
                  <th scope="row">{label}</th>
                  <td>{format(value, "money")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="table-note">
            Expenses shown as positive amounts. Fixed costs include worker and
            rider payroll; incremental costs exclude it.
          </p>
        </section>
      </div>
      <section className="investigate">
        <span className="eyebrow">DECISION CONTEXT</span>
        <div>
          <h2>
            Break-even demand: {format(be.requested_orders_per_day)} orders/day
          </h2>
          <p>
            {reasons[be.reason]} Threshold holds staffing, basket mix and cost
            rates constant.
          </p>
        </div>
        <div>
          <h2>
            Cash burn: {format(cash.monthly_operating_burn, "money")} / month
          </h2>
          <p>
            A steady-state operating estimate. No inventory funding, deposits,
            tax, debt or intra-month payment timing is included.
          </p>
        </div>
      </section>
    </>
  );
}
