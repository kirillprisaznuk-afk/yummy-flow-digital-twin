"""Explicit, reusable baseline/alternative comparisons with undefined-value semantics."""

from decimal import Decimal

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.domain.precision import calculation
from app.domain.results import Comparison, Evaluation, MetricDelta


def _metrics(result: Evaluation) -> dict[str, Decimal | None]:
    return {
        "total_revenue": result.economics.total_revenue,
        "operating_profit": result.economics.operating_profit,
        "contribution_per_order": result.economics.contribution_per_order,
        "contribution_margin": result.economics.contribution_margin,
        "cost_per_order": result.economics.cost_per_order,
        "required_fulfilment_workers": Decimal(result.capacity.required_fulfilment_workers),
        "required_riders": Decimal(result.capacity.required_riders),
        "system_utilisation": result.capacity.system_utilisation,
        "fulfilled_orders_per_day": result.capacity.fulfilled_orders_per_day,
        "break_even_requested_orders_per_day": result.break_even.requested_orders_per_day,
        "static_runway_months": result.cash.static_runway_months,
    }


@calculation
def compare(baseline: Assumptions, alternative: Assumptions) -> Comparison:
    baseline = Assumptions.model_validate(baseline)
    alternative = Assumptions.model_validate(alternative)
    base, alt = evaluate(baseline), evaluate(alternative)
    base_metrics, alt_metrics = _metrics(base), _metrics(alt)
    deltas = {}
    for metric, before in base_metrics.items():
        after = alt_metrics[metric]
        change = after - before if before is not None and after is not None else None
        deltas[metric] = MetricDelta(
            baseline=before,
            alternative=after,
            absolute_change=change,
            relative_change=change / abs(before) if change is not None and before else None,
        )
    return Comparison(
        baseline=base,
        alternative=alt,
        deltas=deltas,
        baseline_operating_days_per_month=baseline.operating_days_per_month,
        alternative_operating_days_per_month=alternative.operating_days_per_month,
        same_operating_days=baseline.operating_days_per_month
        == alternative.operating_days_per_month,
    )
