import type { SimulationResult } from "@/types/model";
import { format } from "@/lib/format";
import { Distribution } from "./charts";
import { inputs } from "./fields";
export function SimulationResults({ m }: { m: SimulationResult }) {
  return (
    <div aria-label="Simulation results" role="region">
      <div className="kpi-strip section-space">
        {[
          ["Probability profitable", format(m.probability_profit, "percent")],
          [
            "Expected result / month",
            format(m.expected_operating_profit, "money"),
          ],
          ["Downside P10", format(m.p10, "money")],
          ["Upside P90", format(m.p90, "money")],
        ].map(([label, value]) => (
          <div key={label}>
            <span className="eyebrow">{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="table-note">
        Simulated, not deterministic · {m.runs.toLocaleString("en-IE")} draws ·
        Seed {m.seed} · Median / P50 {format(m.p50, "money")} · Loss probability{" "}
        {format(m.probability_loss, "percent")} · Exact break-even{" "}
        {format(m.probability_break_even, "percent")}
      </p>
      <Distribution result={m} />
      <h2>Operational risk</h2>
      <dl className="detail-list">
        <div>
          <dt>Probability capacity constrains eligible demand</dt>
          <dd>{format(m.probability_capacity_constraint, "percent")}</dd>
        </div>
        <div>
          <dt>Expected fulfilled orders / day</dt>
          <dd>{format(m.expected_fulfilled_orders_per_day)}</dd>
        </div>
        <div>
          <dt>Expected orders lost to capacity / day</dt>
          <dd>{format(m.expected_capacity_lost_orders_per_day)}</dd>
        </div>
        <div>
          <dt>Expected orders lost to stockouts / day</dt>
          <dd>{format(m.expected_stockout_lost_orders_per_day)}</dd>
        </div>
        <div>
          <dt>Expected total lost orders / day</dt>
          <dd>{format(m.expected_total_lost_orders_per_day)}</dd>
        </div>
        {Object.entries(m.bottleneck_probabilities).map(([key, value]) => (
          <div key={key}>
            <dt>Active {key} bottleneck frequency</dt>
            <dd>{format(value, "percent")}</dd>
          </div>
        ))}
      </dl>
      <p className="table-note">
        Tied resources are counted together, so resource frequencies need not
        sum to 100%. Resource capacities do not change between draws.
      </p>
      <h2 className="section-space">Management interpretation</h2>
      <ul className="risk-insights">
        {m.insights.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
      <details>
        <summary>Sampling bounds and reproducibility record</summary>
        <div className="table-scroll">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Input</th>
                <th>Minimum</th>
                <th>Most likely</th>
                <th>Maximum</th>
                <th>Boundary applied</th>
              </tr>
            </thead>
            <tbody>
              {inputs.map(([key, label]) => {
                const b = m.bounds[key];
                const style =
                  key === "gross_margin"
                    ? "percent"
                    : key === "orders_per_day"
                      ? "number"
                      : "unitmoney";
                return (
                  <tr key={key}>
                    <th>{label}</th>
                    <td>{format(b.low, style)}</td>
                    <td>{format(b.mode, style)}</td>
                    <td>{format(b.high, style)}</td>
                    <td>{b.bounded ? "Yes" : "No"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="table-note">
          Analytics {m.analytics_version}; economic model {m.model_version};
          Python {m.python_version}. Reproduction requires the same scenario,
          settings, run count, seed and software versions. Input sample SHA-256:{" "}
          <code className="digest">{m.sample_digest}</code>
        </p>
      </details>
    </div>
  );
}
