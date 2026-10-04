export default function Methodology() {
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">TRANSPARENT BY DESIGN</span>
          <h1>Methodology</h1>
          <p>Know what the model measures, and where its boundaries sit.</p>
        </div>
        <span className="badge">Calculation model 1.1</span>
      </div>
      <div className="method-grid">
        <section className="panel prose">
          <span className="eyebrow">01 / SCOPE</span>
          <h2>A hypothetical operation</h2>
          <p>
            This is a new portfolio project inspired by questions encountered
            while exploring Yummy Flow in Madrid. It does not represent the
            original venture’s technology or operating results. All inputs are
            synthetic.
          </p>
          <p>
            The model describes one dark store in a steady-state operating
            month. Values are VAT-exclusive EUR. Fractional daily orders are
            expected averages, not individual transactions.
          </p>
        </section>
        <section className="panel prose">
          <span className="eyebrow">02 / CAPACITY</span>
          <h2>Sales follow fulfilled demand</h2>
          <p>
            Stockouts reduce requested demand first. Fulfilled orders are
            limited by the lowest of fulfilment staff capacity, rider capacity,
            and the store throughput ceiling.
          </p>
          <p>
            Staffing represents monthly paid-hour budgets. The delivery cycle
            includes one outbound and return trip plus handoff time. The model
            does not establish a 15-minute service guarantee or model queues and
            hourly peaks.
          </p>
        </section>
        <section className="panel prose">
          <span className="eyebrow">03 / ECONOMICS</span>
          <h2>Keep the cost boundaries clear</h2>
          <p>
            Revenue includes fulfilled product sales and delivery fees. Product
            COGS reflects the basket gross margin. Contribution deducts COGS,
            shrinkage, incremental fulfilment and delivery costs, payment fees
            and acquisition costs.
          </p>
          <p>
            Fixed monthly costs include all paid worker and rider hours, rent,
            utilities and software / administration. Operating result is
            contribution less those fixed costs. Payroll is not charged again in
            per-order incremental costs.
          </p>
        </section>
        <section className="panel prose">
          <span className="eyebrow">04 / BREAK-EVEN & CASH</span>
          <h2>A threshold, not a forecast</h2>
          <p>
            Break-even volume holds basket economics, staffing and other fixed
            costs constant. The backend separately reports whether current
            capacity can reach that threshold. Zero fixed costs or nonpositive
            contribution require special interpretation.
          </p>
          <p>
            Cash runway divides starting cash by operating burn. “No burn” does
            not mean unlimited liquidity. Working capital, deposits, capex, tax,
            debt and payment timing are excluded.
          </p>
        </section>
      </div>
      <section className="panel prose">
        <span className="eyebrow">05 / COMPARISON & PRECISION</span>
        <h2>Read changes in context</h2>
        <p>
          Comparison changes are alternative minus baseline. Margin and
          utilisation changes are percentage points. Undefined values appear as
          —; finite runway cannot be subtracted from a no-burn state. Different
          operating-day counts are explicitly flagged.
        </p>
        <p>
          All financial and operational calculations run in the Python backend.
          It uses decimal monetary rates and exact throughput ratios. This
          interface only formats values, converts percentages for editing and
          scales visual bars. Display rounding never determines break-even
          status.
        </p>
        <p>
          For complete formulas and independent hand-calculated examples, see{" "}
          <code>docs/METHODOLOGY.md</code> and{" "}
          <code>docs/WORKED_EXAMPLE.md</code> in the repository. Forecasting
          remains unimplemented.
        </p>
      </section>
      <section className="panel prose section-space">
        <span className="eyebrow">06 / RISK ANALYSIS · ANALYTICS 1.0</span>
        <h2>Sensitivity holds other assumptions constant</h2>
        <p>
          Requested demand, basket value, gross margin, fulfilment hourly cost,
          incremental delivery cost and rent are individually changed by −20%,
          −10%, +10% and +20%. These are relative changes, including gross
          margin. Inputs are rounded to six decimal places. Invalid cases are
          marked unavailable, never clipped. Ranking uses the maximum minus
          minimum operating result across valid cases, including baseline.
          Unequal valid ranges near input boundaries limit comparability.
        </p>
        <h2>Simulation represents hypothetical monthly states</h2>
        <p>
          Each independent triangular draw uses the scenario value as its
          most-likely input. Default widths are demand ±15%, basket ±8%, gross
          margin ±3 percentage points, and incremental delivery/fulfilment costs
          ±10%. These are illustrative judgement ranges, not fitted confidence
          intervals or measured volatility. Gross margin is bounded to 0–100%;
          other inputs to the model’s nonnegative range. Bounds and samples use
          six decimal places. Boundary adjustments make distributions asymmetric
          and can shift their mean away from baseline.
        </p>
        <p>
          Every draw runs through the same Python capacity and economics engine.
          Staff, opening hours, stockouts and store throughput stay fixed.
          Inputs are independent: correlations, seasonality, growth, shocks
          outside the chosen bounds and daily cash paths are excluded. Capacity
          losses and stockout losses are reported separately.
        </p>
        <h2>Percentiles and probabilities are conditional</h2>
        <p>
          P10 has approximately 10% of simulated operating results below it; P50
          is the median; P90 has approximately 90% below it. They are
          interpolated percentiles, not worst/best cases. Ties can change the
          fraction strictly below a percentile. Profit means result greater than
          zero, loss means less than zero, and exact break-even is reported
          separately. Finite simulation counts introduce sampling variation;
          these frequencies are not validated real-world probabilities.
        </p>
        <h2>Reproduce and interpret responsibly</h2>
        <p>
          The default is 1,000 draws with seed 42; at most 10,000 are allowed. A
          blank seed generates and returns one. Reproduction requires identical
          inputs, settings, count, seed and software versions. The result
          includes Python, model and analytics versions plus an input-sample
          digest. Zero uncertainty reproduces the deterministic model. No
          cash-depletion probability is shown because static runway is not a
          dynamic liquidity model.
        </p>
      </section>
    </>
  );
}
