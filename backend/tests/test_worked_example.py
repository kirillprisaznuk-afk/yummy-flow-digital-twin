"""Independent golden values from docs/WORKED_EXAMPLE.md."""

from decimal import Decimal as D

import pytest

from app.domain.assumptions import Assumptions
from app.domain.comparison import compare
from app.domain.evaluation import evaluate


@pytest.fixture
def worked_example() -> Assumptions:
    return Assumptions(
        orders_per_day=100,
        operating_days_per_month=30,
        operating_hours_per_day=10,
        average_order_value=20,
        delivery_fee=2,
        gross_margin="0.3",
        shrinkage_rate=0,
        stockout_rate=0,
        variable_fulfilment_cost_per_order=1,
        variable_delivery_cost_per_order=2,
        payment_fee_rate=0,
        payment_fee_per_order=0,
        customer_acquisition_cost=0,
        new_customer_order_share=0,
        monthly_rent=2400,
        monthly_utilities=400,
        monthly_software_admin=200,
        fulfilment_workers=2,
        worker_paid_hours_per_month=150,
        worker_hourly_cost=10,
        worker_productive_fraction=1,
        picking_minutes_per_order=2,
        packing_minutes_per_order=1,
        store_orders_per_hour=20,
        riders=6,
        rider_paid_hours_per_month=150,
        rider_hourly_cost=10,
        rider_productive_fraction=1,
        average_delivery_distance_km=1,
        rider_average_speed_kmh=12,
        delivery_handoff_minutes=5,
        starting_cash=6000,
    )


def test_manual_baseline_income_statement_and_capacity(worked_example):
    result = evaluate(worked_example)
    expected = {
        "monthly_fulfilled_orders": 3000,
        "product_revenue": 60000,
        "delivery_revenue": 6000,
        "total_revenue": 66000,
        "product_cogs": 42000,
        "product_gross_profit": 18000,
        "variable_fulfilment_cost": 3000,
        "variable_delivery_cost": 6000,
        "contribution_per_order": 5,
        "contribution": 15000,
        "fulfilment_payroll": 3000,
        "rider_payroll": 9000,
        "total_delivery_cost": 15000,
        "fixed_operating_costs": 15000,
        "total_operating_costs": 66000,
        "cost_per_order": 22,
        "operating_profit": 0,
        "shrinkage_cost": 0,
        "payment_cost": 0,
        "acquisition_cost": 0,
    }
    for metric, value in expected.items():
        assert getattr(result.economics, metric) == value, metric
    assert result.economics.contribution_margin.quantize(D("0.000001")) == D("0.227273")
    assert result.capacity.fulfilment_capacity_per_day == 200
    assert result.capacity.delivery_capacity_per_day == 120
    assert result.capacity.store_capacity_per_day == 200
    assert result.capacity.system_capacity_per_day == 120
    assert result.capacity.system_utilisation.quantize(D("0.000001")) == D("0.833333")
    assert result.capacity.required_fulfilment_workers == 1
    assert result.capacity.required_riders == 5
    assert result.capacity.active_bottlenecks == ()
    assert result.break_even.monthly_fulfilled_orders == 3000
    assert result.break_even.requested_orders_per_day == 100
    assert result.break_even.monthly_revenue == 66000
    assert result.break_even.reachable_at_current_capacity
    assert result.cash.monthly_operating_burn == 0
    assert result.cash.static_runway_months is None


def test_manual_downside_loss_runway_and_comparison(worked_example):
    comparison = compare(worked_example, worked_example.with_changes(orders_per_day=80))
    result = comparison.alternative
    assert result.economics.total_revenue == 52800
    assert result.economics.product_cogs == 33600
    assert result.economics.contribution == 12000
    assert result.economics.operating_profit == -3000
    assert result.economics.cost_per_order == D("23.25")
    assert result.cash.monthly_operating_burn == 3000
    assert result.cash.static_runway_months == 2
    assert comparison.deltas["total_revenue"].absolute_change == -13200
    assert comparison.deltas["total_revenue"].relative_change == D("-0.2")
    assert comparison.deltas["operating_profit"].absolute_change == -3000
    assert comparison.deltas["operating_profit"].relative_change is None


def test_manual_capacity_constrained_upside(worked_example):
    result = evaluate(worked_example.with_changes(orders_per_day=200))
    assert result.capacity.fulfilled_orders_per_day == 120
    assert result.capacity.capacity_lost_orders_per_day == 80
    assert result.capacity.active_bottlenecks == ("delivery",)
    assert result.economics.total_revenue == 79200
    assert result.economics.product_cogs == 50400
    assert result.economics.contribution == 18000
    assert result.economics.fixed_operating_costs == 15000
    assert result.economics.operating_profit == 3000
    assert result.capacity.required_riders == 10
