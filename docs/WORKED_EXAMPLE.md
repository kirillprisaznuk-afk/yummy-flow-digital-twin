# Independent worked example

This intentionally simplified **synthetic** scenario is an arithmetic audit, not a Madrid market estimate. All currency is EUR excluding VAT. The corresponding golden-value regressions are in `backend/tests/test_worked_example.py`; expectations below are hand calculations, not copied engine output.

## Inputs

Requested demand is 100 orders/day, with 30 operating days/month and 10 opening hours/day. Basket value is €20, delivery fee €2, and product gross margin 30%. There are no stockout losses, shrinkage, payment fees, or acquisition costs in this example.

Variable fulfilment costs €1/order; incremental delivery costs €2/order, excluding rider payroll. Two fulfilment workers and six riders each have 150 paid hours/month at €10/hour and 100% productive time. Rent is €2,400, utilities €400, and software/admin €200 per month. Starting cash is €6,000.

Picking takes two minutes and packing one minute. One-way delivery distance is 1 km, average speed 12 km/h, and handoff time five minutes. Store throughput is 20 orders/hour.

## Capacity calculation

- Opening window: 30 × 10 = 300 hours/month; each person's 150 paid hours fit inside it.
- Fulfilment: 2 × 150 × 60 / (3 × 30) = **200 orders/day**.
- Delivery cycle: 5 + (2 × 1 / 12 × 60) = **15 minutes/order**.
- Delivery: 6 × 150 × 60 / (15 × 30) = **120 orders/day**.
- Store: 20 × 10 = **200 orders/day**.
- System: min(200, 120, 200) = **120 orders/day**. Delivery is structurally limiting; demand of 100 is not yet constrained.
- Fulfilled: min(100, 120) = **100/day**, or **3,000/month**. Utilization: fulfilment 50%, delivery 83⅓%, store 50%, system 83⅓%.
- Required worker budgets: ceiling(100 × 30 × 3 / 9,000) = **1**. Required rider budgets: ceiling(100 × 30 × 15 / 9,000) = **5**. Existing staffing remains paid even when fewer budgets would suffice.

## Monthly income statement

| Metric | Hand calculation | Expected |
| --- | --- | ---: |
| Product revenue | 3,000 × €20 | €60,000 |
| Delivery revenue | 3,000 × €2 | €6,000 |
| Total revenue | €60,000 + €6,000 | €66,000 |
| Product COGS | €60,000 × 70% | €42,000 |
| Product gross profit | €60,000 − €42,000 | €18,000 |
| Variable fulfilment | 3,000 × €1 | €3,000 |
| Variable delivery | 3,000 × €2 | €6,000 |
| Contribution | €66,000 − €42,000 − €3,000 − €6,000 | €15,000 |
| Contribution/order | €6 product margin + €2 fee − €1 − €2 | €5 |
| Contribution margin | €15,000 / €66,000 | 22.727273% |
| Fulfilment payroll | 2 × 150 × €10 | €3,000 |
| Rider payroll | 6 × 150 × €10 | €9,000 |
| Other fixed costs | €2,400 + €400 + €200 | €3,000 |
| Total fixed costs | €3,000 + €9,000 + €3,000 | €15,000 |
| Operating result | €15,000 − €15,000 | €0 |
| Total operating costs | €42,000 + €3,000 + €6,000 + €15,000 | €66,000 |
| Cost/fulfilled order | €66,000 / 3,000 | €22 |
| Total delivery cost (informational subtotal) | €9,000 payroll + €6,000 variable | €15,000 |

The delivery subtotal is **not** added again to total costs. Product gross margin is 30%; contribution margin includes delivery revenue and is therefore a different ratio.

Break-even fulfilled orders = €15,000 / €5 = **3,000/month = 100/day**. With no stockouts, requested demand is also 100/day. Break-even revenue = 3,000 × €22 = **€66,000/month**. Capacity of 120/day can reach the threshold. Cash burn is €0/month; static runway is `null` with `no_operating_burn`, not a claim of unlimited liquidity.

## Independent downside and capacity stress checks

At **80 orders/day**, 2,400 monthly orders produce €52,800 revenue, €33,600 COGS, €2,400 variable fulfilment, and €4,800 variable delivery. Contribution is **€12,000**; fixed costs remain €15,000. Operating result is **−€3,000/month**, total costs €55,800, and cost/order €23.25. Starting cash of €6,000 covers **two months** of this simplified burn. Revenue changes by −€13,200 (−20%); profit changes by −€3,000. Relative profit change is undefined because baseline profit is zero.

At **200 requested orders/day**, delivery capacity still permits only 120/day. The model must report **80 unserved orders/day**, 3,600 monthly fulfilled orders, **€79,200 revenue**, €50,400 COGS, €18,000 contribution, and **€3,000 operating profit**. Serving all requested orders would require ten rider budgets, but this calculation does not automatically hire them or change payroll.
