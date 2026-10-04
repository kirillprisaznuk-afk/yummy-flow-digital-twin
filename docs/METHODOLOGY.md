# Model methodology

Start with demand and capacity, then follow the unit-economics table to break-even and cash. Sensitivity and simulation reuse those formulas; they do not replace them. The [portfolio demo](screenshots/README.md) supplies actual API outputs, and the [worked example](WORKED_EXAMPLE.md) provides independent arithmetic.

## Scope and units

This is a deterministic, single-store, steady-state monthly operating model using synthetic assumptions. Currency is EUR, excluding VAT. Demand and throughput are average orders/day; a month has a configurable number of operating days. Percentages are fractions (0.25 = 25%). It is not an accounting statement, valuation, delivery SLA simulation, or observed Yummy Flow performance.

**Calculation version: 1.1.** Version 1.0 had rounding-sensitive break-even classifications and did not identify zero-activity break-even when fixed costs were zero and contribution was nonpositive. Saved 1.0 inputs can be read, but explicit copying into a new 1.1 scenario is required before recalculation. No historical results are silently reinterpreted.

Operating days count trading days within a modeled month, not the calendar length of the month. Reducing trading days reduces demand exposure; it does not prorate monthly rent or contracted paid hours. All monthly financial totals refer to that same type of monthly horizon.

## Demand and capacity

Let D = requested orders/day, s = stockout fraction, N = operating days/month.

- Stockout-lost demand = D × s. Eligible demand = D × (1 − s).
- Available hours/person/month = min(paid monthly hours, opening hours/day × N). Payroll still charges all paid hours, including hours outside the opening window.
- Fulfilment capacity/day = workers × available hours/worker/month × productive fraction × 60 / ((picking minutes + packing minutes) × N).
- Delivery cycle minutes = handoff minutes + 120 × one-way distance km / average speed km/h. This assumes one delivery and a return trip per cycle, without batching.
- Rider capacity/day = riders × available hours/rider/month × productive fraction × 60 / (cycle minutes × N).
- Store capacity/day = maximum store orders/hour × opening hours/day.
- System capacity C = min(fulfilment, rider, store capacities).
- Fulfilled orders/day Q = min(eligible demand, C). Monthly orders = Q × N.
- Capacity-lost orders = eligible demand − Q. Total lost orders = stockout-lost + capacity-lost.
- Resource utilization = Q / resource capacity; undefined (null) at zero capacity. System utilization uses C. A resource can be structurally limiting without actively constraining demand. Report all tied limiting resources; active bottlenecks exist only when eligible demand > C.
- Required workers/riders = ceiling(eligible demand × N × minutes/order / (available monthly hours × productive fraction × 60)). This is the number needed to serve all eligible demand, even if another resource remains constrained.

Workers and riders are full-time-equivalent monthly paid-hour budgets, not simultaneous workers or a shift roster. Productive fractions account for breaks and downtime. This average-capacity approximation does not model hourly peaks, queues, scheduling, traffic, or staffing coverage. Fractional orders are retained as expected averages.

### Operational units and edge checks

| Quantity | Dimensional check | Treatment / edge case |
| --- | --- | --- |
| Worker/rider available minutes | persons × hours/person/month × minutes/hour | Opening hours limit usable time; all contracted hours still incur payroll |
| Fulfilment capacity | minutes/month ÷ minutes/order ÷ days/month = orders/day | Picking is positive, packing may be zero, zero workers means zero capacity |
| Delivery cycle | minutes + (km ÷ km/hour × 60 minutes/hour × 2) | Positive speed and handoff prevent division by zero; zero distance leaves handoff time |
| Delivery capacity | productive rider minutes/month ÷ cycle minutes/order ÷ days/month | Includes return travel and productivity; zero riders means zero capacity |
| Store capacity | orders/hour × opening hours/day | Independent physical ceiling; zero throughput closes the system |
| System capacity / fulfilled orders | Minimum of values all measured in orders/day | No revenue or variable expense is earned on stockout-lost or capacity-lost orders |
| Utilization | fulfilled orders/day ÷ capacity orders/day | Dimensionless, between 0 and 1; null at zero capacity, including zero demand/zero capacity |
| Required budgets | required minutes/month ÷ productive minutes/person/month | Ceiling to whole persons; zero eligible demand needs zero budgets; does not auto-hire |

All tied limiting resources are reported. Exactly meeting capacity is full utilization, not lost demand. Stockout losses are applied first, so they are not counted again as capacity losses. No capacity quantity is a monetary cost by itself.

## Unit economics

Let V = monthly fulfilled orders, A = average basket value, f = delivery fee, g = product gross margin.

| Metric | Formula | Unit / cost treatment |
| --- | --- | --- |
| Product revenue | V × A | EUR/month; fulfilled sales only |
| Delivery revenue | V × f | EUR/month; fee revenue, not a cost offset |
| Total revenue | V × (A + f) | EUR/month; includes each revenue source once |
| Product COGS | V × A × (1 − g) | EUR/month; variable with fulfilled baskets |
| Product gross profit | product revenue − product COGS | EUR/month; excludes delivery revenue |
| Product gross margin | product gross profit / product revenue | Fraction; null when product revenue is zero |
| Shrinkage expense | product revenue × shrinkage fraction | EUR/month; separate variable proxy |
| Variable fulfilment | V × packaging/consumables cost per order | EUR/month; excludes payroll |
| Variable delivery | V × incremental delivery cost per order | EUR/month; excludes payroll |
| Payment costs | V × ((A + f) × payment fraction + payment fixed fee) | EUR/month; transaction costs charged once |
| Acquisition costs | V × new-customer-order fraction × CAC | EUR/month; each new-customer order assumed to acquire one customer |
| Contribution per order c | A × g + f − shrinkage/order − variable fulfilment/order − variable delivery/order − payment/order − acquisition/order | EUR/fulfilled order; excludes fixed payroll |
| Contribution | V × c | EUR/month; before fixed costs |
| Contribution margin | contribution / total revenue | Fraction; null if revenue is zero |
| Fulfilment payroll | workers × monthly paid hours × fully loaded hourly cost | EUR/month; fixed within a scenario |
| Rider payroll | riders × monthly paid hours × fully loaded hourly cost | EUR/month; fixed within a scenario |
| Total delivery cost | rider payroll + variable delivery | EUR/month; informational subtotal, never added again to fixed or total costs |
| Fixed costs F | both payrolls + rent + utilities + software/admin | EUR/month; retained at zero demand |
| Operating result | contribution − F | EUR/month; EBITDA-style proxy |
| Operating margin | operating result / total revenue | Fraction; null at zero revenue |
| At or above break-even | operating result ≥ 0 | Boolean; current scenario status, not a profitability forecast |
| Total operating costs | COGS + shrinkage + variable fulfilment + variable delivery + payment + acquisition + F | EUR/month; each cost charged once |
| Cost per fulfilled order | total operating costs / V | EUR/order; null at zero fulfilled orders |

Product gross margin excludes delivery revenue. Shrinkage is a separate sales-based expense proxy, not a second COGS margin adjustment. Fixed rider payroll and incremental delivery costs are distinct: do not enter an all-inclusive outsourced delivery fee alongside rider wages. Distance reduces rider capacity; this first model does not separately infer fuel costs from distance. Acquisition is an order-mix approximation, not a customer cohort or lifetime-value model.

At zero demand all order-driven amounts are zero, but paid labour and other fixed costs remain. `contribution_per_order` remains the hypothetical next fulfilled order's margin; it is not computed by dividing zero contribution by zero orders. Zero prices, 0% or 100% product margin, and negative contribution are permitted stress scenarios. They must not be interpreted as plausible market inputs. Shrinkage is zero at zero sales in this proxy, which omits losses on idle inventory.

## Decision-view reporting

The API's additive `reporting` section exposes allocations of existing model outputs; it does not change model 1.1 economics or stored assumptions.

- Each per-fulfilled-order component = its monthly EUR amount / monthly fulfilled orders (EUR/order). All allocations are null at zero volume, including fixed costs. The separate hypothetical next-order contribution remains defined according to the unit-economics formula.
- Resource spare capacity = max(0, resource capacity/day − fulfilled orders/day).
- Resource shortfall = max(0, eligible demand/day − resource capacity/day). Stockout losses are excluded; each resource is assessed independently, so these gaps must not be summed as lost demand.
- Additional worker/rider budgets = max(0, required integer FTE budgets − configured budgets). These are staffing requirements, not an automatic hiring recommendation; store throughput and the changed fixed-cost base still need a new scenario.

Allocations use the returned Decimal components at 28 significant digits. They are descriptive reporting values; exact rational classifications in the underlying model remain unchanged. Monthly display rounds to whole EUR and per-order display to cents. The contribution bridge labels subtotals and total-revenue references explicitly to prevent double counting. Fixed allocation per order is not marginal cost.

## Break-even and cash

For F > 0 and c > 0, monthly break-even fulfilled orders = F / c (EUR/month ÷ EUR/order = orders/month); daily threshold = F / (c × N), in orders/day. Required requested demand/day = daily threshold / (1 − s). Break-even monthly revenue = (F / c) × (A + f), in EUR/month, including delivery fees.

These continuous thresholds hold staffing, cost rates, and basket mix fixed. Reachability requires daily threshold ≤ C and s < 1. Zero capacity cannot reach a positive threshold. Total stockouts make the requested threshold undefined; the economic fulfilled-volume threshold still exists. For F > 0 and c ≤ 0, return null thresholds with `nonpositive_contribution`, never infinity.

For F = 0, zero activity already breaks even: all thresholds are zero and the reason is `zero_fixed_costs`, including zero-capacity and total-stockout scenarios. This is not a volume-led viability claim. If c < 0, any positive fulfilment loses money; if c = 0, every volume earns zero operating profit. The current scenario's `is_at_or_above_break_even` still checks its own operating result. Higher staffing is a new scenario with a new fixed-cost base.

Monthly operating burn = max(0, −operating result). Static runway = starting cash / burn when burn > 0, otherwise null with an explicit no-burn status. Zero cash produces zero runway under burn; zero cash is flagged separately even if profitable. This proxy ignores inventory working capital, capex, deposits, taxes, debt, financing, and intra-month payment timing. It is not a liquidity guarantee or a forecast. Growth and uncertain cash paths are outside the final scope.

Burn is EUR/month; runway is EUR ÷ EUR/month = months, potentially fractional. No cash is subtracted twice: fixed and variable cash-like expenses are already represented in the operating result. A profitable result gives zero burn rather than negative burn. `cash_balance_is_zero` describes the starting balance only, not future insolvency.

## Comparisons and precision

Alternative minus baseline gives absolute deltas in the underlying metric's unit. Relative deltas use delta / abs(baseline), and are null for a zero baseline or undefined metric. This sign-normalized relative change makes an improvement from a loss positive; it is not ordinary revenue growth when the baseline is negative. Ratios are fractions; their absolute deltas are percentage-point changes after multiplication by 100. No delta is calculated between a finite runway and a no-burn null value.

Both operating-day counts and `same_operating_days` accompany comparisons. Different trading-day counts change monthly volumes and daily staffing requirements, but both financial totals remain monthly; rent and contracted payroll are not prorated. Comparisons do not automatically resize resources.

Inputs and monetary rates use Decimal. Exact rational arithmetic preserves throughput fractions, staffing ceilings, and break-even comparisons, and scales monetary rates by fractional expected order counts. For example, 9,000 productive minutes/month ÷ 7 minutes/order × EUR 7 contribution/order is exactly EUR 9,000, not a value just above or below it. This prevents false burn or capacity shortfalls at exact thresholds.

Outputs convert to Decimal at 28 significant digits using a local half-even context. No currency-to-cent rounding occurs inside the model; display rounding is a presentation concern. Recurring ratios cannot be represented exactly in finite Decimal strings: independently rounded returned components can differ in their last digit when recombined. Discrete classifications use exact quantities before output conversion, not a rounded UI value or an arbitrary profitability tolerance. Decimal outputs are strings; headcounts and day counts are JSON integers. Assumptions are immutable scalar fields; both `with_changes` and the overridden `model_copy` revalidate edits. Public evaluation revalidates even preconstructed instances.

## Independent verification

See [the worked example](WORKED_EXAMPLE.md) for a hand-calculated monthly statement, capacity calculation, break-even point, downside runway, and capacity stress case. The review also reproduces a recurring-capacity break-even defect that the original passing test suite missed. Formula consistency is not empirical validation of demand, costs, or service reliability.

## Sensitivity analysis — analytics version 1.0

Each of six inputs is perturbed independently by relative −20%, −10%, 0%, +10%, +20%: requested orders/day, average order value, product gross margin, worker hourly cost, incremental delivery cost/order and monthly rent. The existing domain engine evaluates each alternative. Staffing does not automatically resize; demand increases can produce no financial upside once capacity binds.

Tested input = baseline input × (1 + relative change), rounded half-even to six decimal places. Thus 25% margin +20% becomes 30%, not 45%. A zero baseline stays zero. Invalid changes are marked unavailable and excluded, not silently clipped. The API exposes each tested value, complete evaluation, profit delta and unavailability reason. Baseline assumptions are immutable and unchanged.

Impact range = maximum valid operating result − minimum valid operating result, including baseline. Sort descending by that range; ties retain declared variable order and insights name every tied leader. Tornado bars show minimum and maximum profit deltas, not a probability interval. Ranking depends on chosen perturbation sizes and valid bounds; rows with unavailable cases have unequal tested ranges. It is neither causal attribution nor a global sensitivity decomposition.

## Monte Carlo — independent hypothetical monthly states

Five inputs are stochastic: demand, basket value, gross margin, incremental delivery cost and incremental fulfilment cost. Each draw represents one steady-state monthly state using the existing average-day model. It is not a sequence of independently sampled days or months. All other inputs stay fixed, including stockouts, staffing, travel distance, productivity and store capacity.

Distributions are triangular with minimum L, mode M equal to the scenario value, and maximum H. Relative-width inputs use raw bounds M × (1 − w/100), M × (1 + w/100). Gross-margin width is percentage points, so its radius is w/100 added/subtracted from the fraction M. Widths are finite values from 0 to 100. Supports are restricted to [0, 1] for gross margin and [0, 1,000,000,000] for other inputs; these numerical limits are not business recommendations. Report any physical bound adjustment. Bounds and samples round half-even to six decimal places; samples are bounded again after rounding and validated as domain assumptions.

This constructs a triangular distribution on the adjusted support; it does not clamp out-of-bounds normal draws or silently accumulate probability at a boundary. Near a boundary it is asymmetric and its mean need not equal the mode. Zero-width or zero-relative-base inputs are constant. Rounding discretizes the continuous distribution at the model input resolution.

Defaults are illustrative judgement ranges: demand ±15%, basket ±8%, margin ±3 percentage points, incremental delivery and fulfilment ±10%. They are not measured volatility, fitted distributions or confidence intervals. Independence is explicit: no demand/basket/margin correlations are estimated. The bounded support excludes more extreme shocks; assumed ranges can understate risk.

Every draw invokes `evaluate` in memory with validated assumptions. Revenue uses capacity-limited fulfilled demand. Stockout losses are applied before capacity losses. Resource capacities remain fixed; only whether demand exceeds them changes. Active bottleneck frequencies include every tied resource, so they can sum above the system constraint probability. No database query or HTTP request occurs per draw.

### Summaries and interpretation

- Expected profit = arithmetic mean of simulated monthly operating results. Means aggregate returned Decimal outputs through exact rational sums before final Decimal conversion.
- Pq: sort n outcomes; position = (n − 1) × q. Linearly interpolate between the surrounding order statistics. P10 is a downside percentile, P50 is the median, P90 an upside percentile. Approximately 10%/50%/90% lie below these values; ties alter strictly-below proportions. They are not worst/best cases or guaranteed bounds.
- Profit probability = count(profit > 0) / n. Loss probability = count(profit < 0) / n. Exact break-even probability = count(profit = 0) / n. These sum to one.
- Capacity-constraint probability = draws with any active bottleneck / n, using the existing strict eligible-demand > capacity rule.
- Expected fulfilled, capacity-lost and stockout-lost orders/day are sample means. Total lost = capacity-lost + stockout-lost; losses are never counted twice.
- Histogram: 24 equal-width bins from observed minimum to maximum, left-closed/right-open except the final inclusive upper edge. Identical outcomes use one degenerate bin. Chart €0 and percentile markers are references, not additional samples.

These are conditional model frequencies with Monte Carlo sampling error, not empirically validated business probabilities. More runs reduce sampling noise but do not improve unsupported assumptions. There is no cash-depletion probability: static operating runway excludes time paths, working capital and liquidity timing. No LLM is involved in the output-driven management statements.

### Reproducibility and execution limits

Default 1,000 runs and seed 42; UI options are 1,000, 5,000 and 10,000, API bounds 1,000–10,000. Blank/null seed generates an unsigned 32-bit seed and returns it. Each call owns its own `random.Random(seed)` instance; the declared uncertainty-field order fixes draw consumption. Degenerate distributions consume no random draw. Python's standard-library [triangular sampler and reproducibility notes](https://docs.python.org/3.12/library/random.html#random.triangular) define the implementation behavior.

A reproducibility record includes seed, settings, count, Python version, economic model version, analytics version and SHA-256 of the ordered sampled assumption JSON records. Identical scenario/settings/count/seed and software versions reproduce results. Algorithm changes require an analytics-version change; cross-Python-version byte equality is not promised. Decimal trailing zero differences are representational, not numerical changes.

The API permits one active simulation per process and returns a useful 429 response to competing requests. Maximum count bounds CPU/memory; browser disconnect does not cancel an already running calculation. This is local, synchronous analysis, not a distributed job service. Settings/results are ephemeral and are not persisted with scenarios. Frontend results are keyed to the exact selected slot, assumptions and settings to prevent stale attribution.

## Outside the final scope

Forecasting, correlated uncertainty, growth paths, dynamic cash depletion and multi-store expansion are not implemented or promised by this portfolio version.
