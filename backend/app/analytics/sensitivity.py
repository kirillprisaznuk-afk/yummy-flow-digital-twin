"""One-variable-at-a-time analysis through the authoritative domain engine."""

from decimal import Decimal

from pydantic import ValidationError

from app.analytics.contracts import SensitivityPoint, SensitivityResult, SensitivityVariable
from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.domain.precision import calculation

VARIABLES = (
    ("orders_per_day", "Requested orders", "orders/day"),
    ("average_order_value", "Average order value", "EUR/order"),
    ("gross_margin", "Product gross margin", "fraction"),
    ("worker_hourly_cost", "Fulfilment labour rate", "EUR/hour"),
    ("variable_delivery_cost_per_order", "Incremental delivery cost", "EUR/order"),
    ("monthly_rent", "Monthly rent", "EUR/month"),
)


@calculation
def sensitivity(assumptions: Assumptions) -> SensitivityResult:
    a = Assumptions.model_validate(assumptions)
    baseline = evaluate(a)
    variables = []
    for key, label, unit in VARIABLES:
        value = getattr(a, key)
        points = []
        for change in (-20, -10, 0, 10, 20):
            changed = (value * (1 + Decimal(change) / 100)).quantize(Decimal("0.000001"))
            try:
                result = baseline if change == 0 else evaluate(a.with_changes(**{key: changed}))
            except ValidationError:
                points.append(
                    SensitivityPoint(
                        change_percent=change,
                        value=changed,
                        result=None,
                        operating_profit_delta=None,
                        unavailable_reason="Outside model bounds; not evaluated or clipped.",
                    )
                )
                continue
            points.append(
                SensitivityPoint(
                    change_percent=change,
                    value=changed,
                    result=result,
                    operating_profit_delta=result.economics.operating_profit
                    - baseline.economics.operating_profit,
                )
            )
        deltas = [p.operating_profit_delta for p in points if p.operating_profit_delta is not None]
        variables.append(
            SensitivityVariable(
                key=key,
                label=label,
                unit=unit,
                baseline_value=value,
                points=points,
                impact_range=max(deltas) - min(deltas),
                downside_delta=min(deltas),
                upside_delta=max(deltas),
            )
        )
    variables.sort(key=lambda v: v.impact_range, reverse=True)
    top = variables[0].impact_range
    leaders = ", ".join(v.label for v in variables if v.impact_range == top)
    insight = (
        f"{leaders}: largest tested operating-result range (EUR {top:,.0f}/month)."
        if top
        else "None of the tested perturbations changes operating result."
    )
    return SensitivityResult(
        baseline=baseline,
        variables=variables,
        insights=[
            insight,
            "Ranking measures the specified valid perturbations, not causality or probability. "
            "Demand upside can flatten when capacity is binding; staffing stays fixed.",
        ],
    )
