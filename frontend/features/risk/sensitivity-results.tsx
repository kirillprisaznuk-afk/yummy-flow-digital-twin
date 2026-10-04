import type { SensitivityResult } from "@/types/model";
import { format } from "@/lib/format";
import { Tornado } from "./charts";
export function SensitivityResults({ s }: { s: SensitivityResult }) {
  return (
    <>
      <Tornado result={s} />
      <div className="table-scroll">
        <table className="comparison-table">
          <caption>
            Monthly operating result · EUR. — indicates an out-of-bounds case,
            excluded from the ranking.
          </caption>
          <thead>
            <tr>
              <th>Variable / baseline input</th>
              {["−20%", "−10%", "Baseline", "+10%", "+20%", "Impact range"].map(
                (h) => (
                  <th key={h}>{h}</th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {s.variables.map((v) => (
              <tr key={v.key}>
                <th scope="row">
                  {v.label}
                  <small>
                    {format(
                      v.baseline_value,
                      v.unit === "fraction" ? "percent" : "number",
                    )}{" "}
                    {v.unit === "fraction" ? "" : v.unit}
                  </small>
                </th>
                {v.points.map((p) => (
                  <td
                    key={p.change_percent}
                    title={p.unavailable_reason || undefined}
                  >
                    {p.result
                      ? format(p.result.economics.operating_profit, "money")
                      : "—"}
                  </td>
                ))}
                <td>{format(v.impact_range, "money")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details className="section-space">
        <summary>
          Inspect tested inputs, margins, break-even and utilisation
        </summary>
        <div className="table-scroll">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Variable / change</th>
                <th>Tested input</th>
                <th>Contribution margin</th>
                <th>Contribution / order</th>
                <th>At / above break-even</th>
                <th>System utilisation</th>
              </tr>
            </thead>
            <tbody>
              {s.variables.flatMap((v) =>
                v.points.map((p) => (
                  <tr key={`${v.key}-${p.change_percent}`}>
                    <th>
                      {v.label} ({p.change_percent}%)
                    </th>
                    <td>
                      {format(
                        p.value,
                        v.unit === "fraction" ? "percent" : "number",
                      )}{" "}
                      {v.unit === "fraction" ? "" : v.unit}
                    </td>
                    <td>
                      {format(
                        p.result?.economics.contribution_margin ?? null,
                        "percent",
                      )}
                    </td>
                    <td>
                      {format(
                        p.result?.economics.contribution_per_order ?? null,
                        "unitmoney",
                      )}
                    </td>
                    <td>
                      {p.result
                        ? p.result.economics.is_at_or_above_break_even
                          ? "Yes"
                          : "No"
                        : "Not evaluated"}
                    </td>
                    <td>
                      {format(
                        p.result?.capacity.system_utilisation ?? null,
                        "percent",
                      )}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </details>
      <ul className="risk-insights">
        {s.insights.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
    </>
  );
}
