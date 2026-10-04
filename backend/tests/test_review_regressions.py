"""Failures reproduced during the skeptical review, not coverage filler."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.assumptions import Assumptions
from app.domain.comparison import compare
from app.domain.economics import calculate_economics
from app.domain.evaluation import evaluate


def test_recurring_capacity_does_not_turn_exact_break_even_into_a_shortfall():
    # 150 productive hours = 9,000 minutes. At 7 minutes/order and EUR 7
    # contribution/order, maximum monthly contribution is exactly EUR 9,000.
    a = Assumptions(
        orders_per_day=100,
        stockout_rate=0,
        average_order_value=20,
        delivery_fee=1,
        gross_margin="0.3",
        shrinkage_rate=0,
        variable_fulfilment_cost_per_order=0,
        variable_delivery_cost_per_order=0,
        payment_fee_rate=0,
        payment_fee_per_order=0,
        customer_acquisition_cost=0,
        monthly_rent=7500,
        monthly_utilities=0,
        monthly_software_admin=0,
        fulfilment_workers=1,
        worker_paid_hours_per_month=150,
        worker_hourly_cost=10,
        worker_productive_fraction=1,
        picking_minutes_per_order=7,
        packing_minutes_per_order=0,
        rider_hourly_cost=0,
    )
    result = evaluate(a)
    assert result.economics.operating_profit == 0
    assert result.break_even.reachable_at_current_capacity
    assert result.cash.monthly_operating_burn == 0
    assert result.cash.static_runway_months is None


@pytest.mark.parametrize("unit_cost", ["7", "8"])
def test_zero_fixed_costs_has_zero_activity_break_even_even_without_positive_margin(unit_cost):
    a = Assumptions(
        orders_per_day=0,
        average_order_value=20,
        gross_margin="0.3",
        delivery_fee=1,
        shrinkage_rate=0,
        variable_fulfilment_cost_per_order=0,
        variable_delivery_cost_per_order=unit_cost,
        payment_fee_rate=0,
        payment_fee_per_order=0,
        customer_acquisition_cost=0,
        worker_hourly_cost=0,
        rider_hourly_cost=0,
        monthly_rent=0,
        monthly_utilities=0,
        monthly_software_admin=0,
    )
    result = evaluate(a)
    assert result.economics.operating_profit == 0
    assert result.break_even.monthly_fulfilled_orders == 0
    assert result.break_even.reachable_at_current_capacity
    assert result.break_even.reason == "zero_fixed_costs"
    # Negative contribution still means that growth destroys value.
    assert evaluate(a.with_changes(orders_per_day=1)).economics.operating_profit <= 0


def test_public_economics_entrypoint_cannot_bypass_capacity():
    result = calculate_economics(Assumptions(riders=0))
    assert result.monthly_fulfilled_orders == 0
    assert result.total_revenue == 0
    assert result.operating_profit == -result.fixed_operating_costs


def test_model_copy_revalidates_and_does_not_modify_the_original():
    original = Assumptions()
    with pytest.raises(ValidationError):
        original.model_copy(update={"gross_margin": 2})
    revised = original.model_copy(update={"orders_per_day": "123"})
    assert revised.orders_per_day == Decimal(123)
    assert original.orders_per_day == 700


def test_unvalidated_constructed_models_cannot_enter_evaluation():
    with pytest.raises(ValidationError):
        evaluate(Assumptions.model_construct(orders_per_day=Decimal(-1)))


def test_different_operating_day_counts_are_visible_in_comparison_results(assumptions):
    comparison = compare(assumptions, assumptions.with_changes(operating_days_per_month=20))
    assert comparison.baseline_operating_days_per_month == 30
    assert comparison.alternative_operating_days_per_month == 20
    assert not comparison.same_operating_days


def test_zero_demand_and_zero_resources_do_not_invent_utilisation_or_staff():
    result = evaluate(
        Assumptions(orders_per_day=0, fulfilment_workers=0, riders=0, store_orders_per_hour=0)
    )
    assert result.capacity.system_utilisation is None
    assert result.capacity.active_bottlenecks == ()
    assert result.capacity.required_fulfilment_workers == result.capacity.required_riders == 0
    assert result.economics.operating_profit == -7900
    assert result.break_even.reason == "capacity_shortfall"


@pytest.mark.parametrize(
    "margin,cogs,contribution,profit",
    [
        ("0", 60000, -3720, -23020),
        ("1", 0, 56280, 36980),
    ],
)
def test_valid_gross_margin_endpoints(assumptions, margin, cogs, contribution, profit):
    result = evaluate(assumptions.with_changes(gross_margin=margin)).economics
    assert result.product_cogs == cogs
    assert result.product_gross_margin == Decimal(margin)
    assert result.contribution == contribution
    assert result.operating_profit == profit
