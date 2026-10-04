"use client";
import { SelectedResults } from "@/components/selected-results";
import { format } from "@/lib/format";
const rows = [
  ["product_revenue", "Product sales / average order value", "revenue"],
  ["product_cogs", "Product cost of goods", "cost"],
  ["product_gross_profit", "Product gross profit", "subtotal"],
  ["delivery_revenue", "Delivery fee revenue", "revenue"],
  ["total_revenue", "Total revenue · product sales + fees", "reference"],
  ["shrinkage_cost", "Shrinkage / wastage", "cost"],
  [
    "variable_fulfilment_cost",
    "Incremental fulfilment · packaging & consumables",
    "cost",
  ],
  ["variable_delivery_cost", "Incremental delivery · excludes payroll", "cost"],
  ["payment_cost", "Payment processing", "cost"],
  ["acquisition_cost", "Acquisition · weighted by new-customer orders", "cost"],
  ["contribution", "Contribution before fixed costs", "subtotal"],
  [
    "fixed_operating_costs",
    "Fixed operating costs · includes all payroll",
    "cost",
  ],
  ["operating_profit", "Operating result", "subtotal"],
] as const;
export default function Economics() {
  return (
    <SelectedResults title="Unit Economics">
      {(r) => (
        <>
          <div className="kpi-strip">
            <div>
              <span className="eyebrow">MONTHLY FULFILLED ORDERS</span>
              <strong>{format(r.economics.monthly_fulfilled_orders)}</strong>
            </div>
            <div>
              <span className="eyebrow">CONTRIBUTION / ORDER</span>
              <strong>
                {format(r.economics.contribution_per_order, "unitmoney")}
              </strong>
              <small>Modelled next fulfilled order</small>
            </div>
            <div>
              <span className="eyebrow">CONTRIBUTION MARGIN</span>
              <strong>
                {format(r.economics.contribution_margin, "percent")}
              </strong>
            </div>
            <div>
              <span className="eyebrow">OPERATING RESULT / MONTH</span>
              <strong>{format(r.economics.operating_profit, "money")}</strong>
            </div>
          </div>
          <section className="panel section-space">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">REVENUE → CONTRIBUTION → RESULT</span>
                <h2>Monthly and per-order contribution bridge</h2>
              </div>
              <span className="unit-label">VAT-exclusive EUR</span>
            </div>
            <div className="table-scroll">
              <table className="comparison-table economics-bridge">
                <caption>
                  Expenses are positive deductions. Subtotals and reference rows
                  are not additional costs.
                </caption>
                <thead>
                  <tr>
                    <th>Component</th>
                    <th>Treatment</th>
                    <th>Monthly</th>
                    <th>Per fulfilled order</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(([key, label, kind]) => (
                    <tr
                      key={key}
                      className={kind === "subtotal" ? "bridge-total" : ""}
                    >
                      <th scope="row">{label}</th>
                      <td>
                        {kind === "cost"
                          ? "Deduct"
                          : kind === "revenue"
                            ? "Revenue"
                            : kind === "reference"
                              ? "Reference only"
                              : "Subtotal"}
                      </td>
                      <td>{format(r.economics[key], "money")}</td>
                      <td>
                        {format(
                          r.reporting.per_fulfilled_order[key],
                          "unitmoney",
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="table-note">
              Per-order allocations are computed by the backend as each monthly
              component ÷ monthly fulfilled orders. They are undefined at zero
              volume. Product sales per order equal basket value when orders are
              fulfilled. Acquisition per order is the weighted cost, not the
              full acquisition cost for every order.
            </p>
          </section>
          <div className="method-grid section-space">
            <section className="panel prose">
              <h2>Fixed-cost allocation is not marginal cost</h2>
              <p>
                Payroll, rent, utilities and administration remain monthly fixed
                costs. Allocating them per fulfilled order helps compare scale;
                it does not make these costs variable. Rider payroll is already
                in fixed costs and is not added again as incremental delivery
                cost.
              </p>
              <p>
                Fulfilment payroll:{" "}
                {format(r.economics.fulfilment_payroll, "money")} / month. Rider
                payroll: {format(r.economics.rider_payroll, "money")} / month.
              </p>
            </section>
            <section className="panel prose">
              <h2>Zero volume and rounding</h2>
              <p>
                At zero fulfilled volume, — means a per-order allocation is
                undefined. The modelled contribution for a hypothetical next
                fulfilled order can still be shown above, even while current
                monthly contribution is zero.
              </p>
              <p>
                Monthly values display whole euros; per-order values display
                cents. Rounded table rows may not sum exactly. Cash investment,
                tax, depreciation, financing and inventory working capital
                remain excluded.
              </p>
            </section>
          </div>
        </>
      )}
    </SelectedResults>
  );
}
