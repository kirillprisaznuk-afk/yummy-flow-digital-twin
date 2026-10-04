from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from app.domain.assumptions import Assumptions
from app.domain.comparison import compare
from app.domain.evaluation import evaluate


@pytest.mark.parametrize(
    "field,value",
    [
        ("orders_per_day", -1),
        ("gross_margin", "1.01"),
        ("gross_margin", "-0.1"),
        ("worker_hourly_cost", -1),
        ("starting_cash", -1),
        ("stockout_rate", 2),
        ("fulfilment_workers", 1.5),
        ("fulfilment_workers", True),
        ("riders", -1),
        ("operating_days_per_month", 0),
        ("operating_days_per_month", 32),
        ("operating_hours_per_day", 25),
        ("operating_hours_per_day", "NaN"),
        ("worker_paid_hours_per_month", 0),
        ("rider_paid_hours_per_month", 241),
        ("worker_productive_fraction", 0),
        ("rider_productive_fraction", "1.1"),
        ("picking_minutes_per_order", 0),
        ("packing_minutes_per_order", -1),
        ("rider_average_speed_kmh", 0),
        ("delivery_handoff_minutes", 0),
        ("orders_per_day", "NaN"),
        ("orders_per_day", "Infinity"),
        ("monthly_rent", "-Infinity"),
        ("monthly_rent", True),
        ("unknown_field", 1),
    ],
)
def test_invalid_inputs_are_rejected(field, value):
    with pytest.raises(ValidationError):
        Assumptions(**{field: value})


def test_defaults_are_valid_and_immutable():
    assumptions = Assumptions()
    assert isinstance(assumptions.orders_per_day, D)
    assert evaluate(assumptions).data_classification == "illustrative_synthetic"
    with pytest.raises(ValidationError):
        assumptions.orders_per_day = D(10)
    with pytest.raises(ValidationError):
        assumptions.with_changes(gross_margin=2)


def test_comparison_includes_operating_tradeoffs(assumptions):
    result = compare(assumptions, assumptions.with_changes(orders_per_day=200))
    assert result.deltas["total_revenue"].absolute_change == 66000
    assert result.deltas["total_revenue"].relative_change == 1
    assert result.deltas["operating_profit"].absolute_change == 14280
    assert result.deltas["operating_profit"].relative_change == D(14280) / 5020
    assert result.deltas["required_riders"].absolute_change == 5
    assert result.deltas["required_fulfilment_workers"].absolute_change == 1
    assert result.deltas["system_utilisation"].absolute_change == D("0.5")
    assert result.deltas["static_runway_months"].absolute_change is None
    assert result.alternative.economics.is_at_or_above_break_even
    assert not result.baseline.economics.is_at_or_above_break_even


def test_comparison_does_not_divide_by_zero_or_subtract_unknown_values(assumptions):
    result = compare(assumptions.with_changes(orders_per_day=0), assumptions)
    assert result.deltas["total_revenue"].relative_change is None
    assert result.deltas["cost_per_order"].absolute_change is None


def test_additional_demand_above_capacity_does_not_raise_revenue(assumptions):
    result = compare(
        assumptions.with_changes(orders_per_day=300), assumptions.with_changes(orders_per_day=390)
    )
    assert result.deltas["total_revenue"].absolute_change == 0
    assert result.deltas["operating_profit"].absolute_change == 0
    assert result.deltas["required_riders"].absolute_change > 0


def test_identical_scenarios_have_zero_defined_deltas(assumptions):
    result = compare(assumptions, assumptions)
    assert all(delta.absolute_change == 0 for delta in result.deltas.values())
