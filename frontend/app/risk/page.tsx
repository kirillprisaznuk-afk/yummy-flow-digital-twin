"use client";
import { SelectedResults } from "@/components/selected-results";
import { RiskWorkspace } from "@/features/risk/workspace";
import { format } from "@/lib/format";

export default function Risk() {
  return (
    <SelectedResults title="Risk & Simulation">
      {(r) => (
        <>
          <section className="panel">
            <span className="eyebrow">
              DETERMINISTIC SELECTED SCENARIO · BEFORE UNCERTAINTY
            </span>
            <dl className="detail-list">
              <div>
                <dt>Monthly operating result</dt>
                <dd>{format(r.economics.operating_profit, "money")}</dd>
              </div>
              <div>
                <dt>Fulfilled orders / day</dt>
                <dd>{format(r.capacity.fulfilled_orders_per_day)}</dd>
              </div>
              <div>
                <dt>System utilisation</dt>
                <dd>{format(r.capacity.system_utilisation, "percent")}</dd>
              </div>
            </dl>
          </section>
          <RiskWorkspace />
        </>
      )}
    </SelectedResults>
  );
}
