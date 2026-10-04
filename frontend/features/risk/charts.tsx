import type { SensitivityResult, SimulationResult } from "@/types/model";
import { format } from "@/lib/format";

export function Tornado({ result }: { result: SensitivityResult }) {
  // Geometry only: all deltas and rankings were calculated by Python.
  const extent = Math.max(
    1,
    ...result.variables.flatMap((v) => [
      Math.abs(Number(v.downside_delta)),
      Math.abs(Number(v.upside_delta)),
    ]),
  );
  return (
    <figure className="risk-chart">
      <figcaption>
        Operating-result change from deterministic baseline · EUR/month
      </figcaption>
      <div className="tornado-axis">
        <span>Lower profit</span>
        <span>€0 change</span>
        <span>Higher profit</span>
      </div>
      {result.variables.map((v) => (
        <div className="tornado-row" key={v.key}>
          <strong>{v.label}</strong>
          <div
            className="tornado-track"
            role="img"
            aria-label={`${v.label}: ${format(v.downside_delta, "money")} to ${format(v.upside_delta, "money")} monthly change`}
          >
            <span className="tornado-zero" />
            <span
              className="tornado-down"
              style={{
                right: "50%",
                width: `${(Math.abs(Number(v.downside_delta)) / extent) * 50}%`,
              }}
            />
            <span
              className="tornado-up"
              style={{
                left: "50%",
                width: `${(Number(v.upside_delta) / extent) * 50}%`,
              }}
            />
          </div>
          <span>
            {format(v.downside_delta, "money")} →{" "}
            {format(v.upside_delta, "money")}
          </span>
        </div>
      ))}
      <p className="table-note">
        Ranked by maximum minus minimum operating result across valid tested
        cases. Bar colours indicate outcome direction, not whether the input
        increased. Zero bars can reflect binding capacity or a zero baseline
        input.
      </p>
    </figure>
  );
}

export function Distribution({ result }: { result: SimulationResult }) {
  const bins = result.histogram;
  const low = Math.min(0, Number(bins[0].lower));
  const high = Math.max(0, Number(bins[bins.length - 1].upper));
  const span = high - low || 1;
  const x = (value: string | number) =>
    55 + ((Number(value) - low) / span) * 800;
  const peak = Math.max(1, ...bins.map((b) => b.count));
  const markers = [
    ["P10", result.p10],
    ["P50", result.p50],
    ["P90", result.p90],
    ["Break-even", "0"],
  ];
  return (
    <figure className="risk-chart">
      <figcaption>
        Simulated monthly operating result · EUR · bar heights show draw counts
      </figcaption>
      <div className="risk-plot-scroll">
        <svg
          viewBox="0 0 920 340"
          role="img"
          aria-label="Histogram of simulated monthly operating result, with P10, P50, P90 and zero break-even markers"
        >
          <text x="5" y="130">
            {peak}
          </text>
          <text x="30" y="284">
            0
          </text>
          {bins.map((b, i) => (
            <rect
              key={i}
              x={x(b.lower)}
              y={280 - (b.count / peak) * 150}
              width={Math.max(2, x(b.upper) - x(b.lower) - 1)}
              height={(b.count / peak) * 150}
              fill="#648d7b"
            >
              <title>
                {format(b.lower, "money")} to {format(b.upper, "money")}:{" "}
                {b.count} draws
              </title>
            </rect>
          ))}
          {markers.map(([label, value], i) => (
            <g key={label}>
              <line
                x1={x(value)}
                x2={x(value)}
                y1={20 + i * 25}
                y2="280"
                stroke={i === 3 ? "#a63837" : "#263d35"}
                strokeDasharray="4 3"
              />
              <text
                x={Math.max(140, Math.min(770, x(value)))}
                y={16 + i * 25}
                textAnchor="middle"
              >
                {label} · {format(value, "money")}
              </text>
            </g>
          ))}
          <line x1="55" x2="855" y1="280" y2="280" stroke="#617171" />
          <text x="55" y="310">
            {format(low, "money")}
          </text>
          <text x="855" y="310" textAnchor="end">
            {format(high, "money")}
          </text>
        </svg>
      </div>
      <p className="table-note">
        P10: approximately 10% of draws are lower. P50: median. P90:
        approximately 90% are lower. These are not guaranteed bounds or
        worst/best cases. Identical outcomes form one bar; ties can make
        percentile markers coincide.
      </p>
      <details>
        <summary>Accessible histogram counts</summary>
        <div className="table-scroll">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>From EUR</th>
                <th>To EUR</th>
                <th>Draws</th>
              </tr>
            </thead>
            <tbody>
              {bins.map((b, i) => (
                <tr key={i}>
                  <td>{format(b.lower, "money")}</td>
                  <td>{format(b.upper, "money")}</td>
                  <td>{b.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
