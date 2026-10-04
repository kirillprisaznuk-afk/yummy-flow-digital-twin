"use client";
import { SelectedResults } from "@/components/selected-results";
import { format } from "@/lib/format";
export default function Operations() {
  return (
    <SelectedResults title="Operations">
      {(r, draft) => {
        const c = r.capacity;
        const a = draft.assumptions;
        const resources = [
          {
            key: "fulfilment" as const,
            label: "Fulfilment staff",
            capacity: c.fulfilment_capacity_per_day,
            utilisation: c.fulfilment_utilisation,
          },
          {
            key: "delivery" as const,
            label: "Delivery riders",
            capacity: c.delivery_capacity_per_day,
            utilisation: c.delivery_utilisation,
          },
          {
            key: "store" as const,
            label: "Store throughput",
            capacity: c.store_capacity_per_day,
            utilisation: c.store_utilisation,
          },
        ];
        return (
          <>
            <div className="kpi-strip">
              <div>
                <span className="eyebrow">REQUESTED DEMAND / DAY</span>
                <strong>{format(c.requested_orders_per_day)}</strong>
              </div>
              <div>
                <span className="eyebrow">ELIGIBLE AFTER STOCKOUTS</span>
                <strong>{format(c.eligible_orders_per_day)}</strong>
              </div>
              <div>
                <span className="eyebrow">FULFILLED / DAY</span>
                <strong>{format(c.fulfilled_orders_per_day)}</strong>
              </div>
              <div>
                <span className="eyebrow">SYSTEM CAPACITY / DAY</span>
                <strong>{format(c.system_capacity_per_day)}</strong>
              </div>
            </div>
            <section className="model-note">
              <h2>
                {c.active_bottlenecks.length
                  ? `Active bottleneck: ${c.active_bottlenecks.join(" + ")}`
                  : "No active capacity bottleneck"}
              </h2>
              <p>{c.explanation}</p>
              <p>
                Structurally limiting resource:{" "}
                {c.limiting_resources.join(" + ")}. A structural limit is not an
                active shortfall when demand fits within it.
              </p>
            </section>
            <section className="panel section-space">
              <h2>Capacity by resource</h2>
              <div className="table-scroll">
                <table className="comparison-table">
                  <caption>
                    Orders/day. Utilisation = fulfilled orders ÷ resource
                    capacity.
                  </caption>
                  <thead>
                    <tr>
                      <th>Resource</th>
                      <th>Capacity</th>
                      <th>Utilisation</th>
                      <th>Spare after fulfilment</th>
                      <th>Shortfall to eligible demand</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resources.map((item) => (
                      <tr key={item.key}>
                        <th scope="row">{item.label}</th>
                        <td>{format(item.capacity)}</td>
                        <td>{format(item.utilisation, "percent")}</td>
                        <td>
                          {format(
                            r.reporting.resource_gaps[item.key]
                              .spare_after_fulfilment,
                          )}
                        </td>
                        <td>
                          {format(
                            r.reporting.resource_gaps[item.key]
                              .shortfall_to_eligible_demand,
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="table-note">
                Spare resource capacity cannot bypass a different resource’s
                bottleneck. — means utilisation is undefined at zero capacity.
              </p>
            </section>
            <div className="method-grid section-space">
              <section className="panel">
                <h2>Unserved requested demand</h2>
                <dl className="detail-list">
                  <div>
                    <dt>Lost to stockouts / day</dt>
                    <dd>{format(c.stockout_lost_orders_per_day)}</dd>
                  </div>
                  <div>
                    <dt>Lost to capacity / day</dt>
                    <dd>{format(c.capacity_lost_orders_per_day)}</dd>
                  </div>
                </dl>
                <p className="table-note">
                  Stockout losses are removed first and never counted again as
                  capacity loss. Staffing alone does not recover stockout
                  losses.
                </p>
              </section>
              <section className="panel">
                <h2>Resources to serve eligible demand</h2>
                <div className="table-scroll">
                  <table className="comparison-table staffing-table">
                    <thead>
                      <tr>
                        <th>Monthly FTE budget</th>
                        <th>Current</th>
                        <th>Required</th>
                        <th>Additional</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <th>Fulfilment</th>
                        <td>{a.fulfilment_workers}</td>
                        <td>{c.required_fulfilment_workers}</td>
                        <td>{r.reporting.additional_fulfilment_workers}</td>
                      </tr>
                      <tr>
                        <th>Riders</th>
                        <td>{a.riders}</td>
                        <td>{c.required_riders}</td>
                        <td>{r.reporting.additional_riders}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="table-note">
                  Requirements cover demand after stockouts, not all requested
                  orders. Hiring changes fixed costs and requires a new
                  scenario; the store ceiling must also be sufficient.
                </p>
              </section>
            </div>
            <section className="panel prose">
              <h2>Operational limits of this model</h2>
              <p>
                Average daily throughput uses monthly paid-hour budgets and
                productive-time assumptions. It is not a shift roster, queueing
                model or service-level guarantee. Delivery assumes one outbound
                and return trip plus handoff, without batching, traffic or
                hourly peaks.
              </p>
              <p>
                Calculated delivery cycle: {format(c.delivery_cycle_minutes)}{" "}
                minutes. These cycle averages do not validate a 15-minute
                customer delivery promise.
              </p>
            </section>
          </>
        );
      }}
    </SelectedResults>
  );
}
