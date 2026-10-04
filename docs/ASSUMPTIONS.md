# Synthetic assumptions register

All numbers below are illustrative inputs for a hypothetical Madrid dark store. They are not observed Yummy Flow operating data, market benchmarks, employment-law guidance, or claims about competitors. Defaults are centralized in `backend/app/domain/assumptions.py`; this register explains their role. Currency is EUR excluding VAT; hourly costs are assumed fully loaded employer costs.

## Synthetic default values

| Inputs | Defaults | Rationale / interpretation |
| --- | --- | --- |
| Requested orders/day | 700 | A busy illustrative store that exposes a delivery constraint |
| Operating days/month; opening hours/day | 30; 16 | A standardized month, not a staffing rota or calendar forecast |
| Basket value; delivery fee | €28; €1.99 | Grocery basket revenue and fee shown separately |
| Product gross margin | 25% | Assumed merchandise margin before shrinkage and operations |
| Shrinkage; stockout rate | 1%; 2% | Separate sales-based expense and lost-order assumptions |
| Variable fulfilment; incremental delivery/order | €0.35; €0.50 | Consumables and incremental delivery expense, excluding paid labour |
| Payment rate; fixed transaction fee | 2%; €0.10 | Charged on basket plus delivery fee |
| CAC; new-customer-order share | €8; 5% | Acquisition expense allocated only to the assumed new-customer order mix |
| Monthly rent; utilities; software/admin | €6,500; €900; €500 | Fixed store expenses; no property-market evidence implied |
| Fulfilment workers; riders | 12; 36 | Monthly FTE budgets, not concurrent on-shift headcount |
| Monthly paid hours/person | 160 for each role | Paid-hour budgets; opening hours cap usable hours |
| Hourly worker; rider costs | €14; €13 | Fully loaded synthetic rates, not salary estimates or legal minima |
| Productive fraction | 85% for each role | Usable working time after downtime/breaks |
| Picking; packing time/order | 3; 1 minutes | Four minutes of productive fulfilment work |
| Physical store throughput/hour | 80 | Independent space/equipment throughput ceiling |
| One-way delivery distance; average speed | 1.5 km; 18 km/h | Simplified constant-distance return-trip model |
| Handoff/service time | 5 minutes | Non-travel part of each delivery cycle |
| Starting cash | €150,000 | Cash available for the simplified operating-burn calculation |

## Modelling conventions and validation

Inputs are finite, nonnegative where appropriate, and accept at most six decimal places. Rates are bounded to [0, 1], productive fractions and service-time denominators are positive, headcounts are whole FTE budgets, opening hours are at most 24/day, and paid hours are at most 240/month. Broad numerical caps protect calculations; they are not recommended business ranges. Unknown input fields are rejected.

For clarity, `gross_margin`, `shrinkage_rate`, `stockout_rate`, payment rates, and productive fractions are all decimal fractions, not percentage points. Fractional expected orders are valid; headcounts cannot be fractional or booleans. Trading days can differ between scenarios while monthly rent and contracted paid hours remain fixed. Staff below the required level and capacity below demand are intentionally valid scenarios, with losses reported rather than inputs rejected.

## Acknowledged simplifications

There is no empirical plausibility validator: free delivery, zero wages, very low demand, and extreme positive travel/service inputs may be used for stress testing. Positive denominators avoid undefined capacity, but do not establish a feasible roster, route, or SLA. Paid hours exceeding opening hours still cost money while only the opening window contributes capacity. Combining all-inclusive outsourced delivery fees with paid riders would double-count labour; the model supports incremental delivery cost, not automatic outsourcing mode detection.

## Calculation assumptions and demo interpretation

The default model yields 816 fulfilment, 652.8 delivery, and 1,280 store orders/day of average capacity. Of 700 requested orders, 14 are lost to stockouts and 33.2 to delivery capacity. Fractional orders represent expected averages. The resulting profitability is a consequence of the selected inputs, not evidence of commercial viability.

Model 1.1 retains these default assumptions. Its corrections concern exact arithmetic at boundaries and validation, not calibration. See [the independent worked example](WORKED_EXAMPLE.md) for intentionally simpler inputs with a hand-verifiable result.

Monthly growth paths, time-varying volatility, customer cohorts, inventory replenishment, working capital, hourly peaks, routing, multi-store effects and demand history are outside the final scope. Monte Carlo varies static monthly assumptions; it does not model a time series. No historical dataset is supplied.


## Illustrative uncertainty settings

Analytics defaults live in `backend/app/analytics/contracts.py`: 1,000 draws, seed 42, demand ±15%, basket ±8%, gross margin ±3 percentage points, and incremental delivery/fulfilment costs ±10%. Each triangular distribution uses the selected scenario value as its mode; inputs are independent and supports respect domain bounds. These are synthetic judgement ranges, not empirical parameter estimates. Unchanged staffing and stockout assumptions are deliberate limitations. See [methodology](METHODOLOGY.md) before interpreting probabilities.
