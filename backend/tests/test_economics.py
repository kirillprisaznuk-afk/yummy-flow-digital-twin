from decimal import ROUND_DOWN, localcontext
from decimal import Decimal as D

import pytest

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate


def test_hand_calculated_monthly_statement(assumptions):
    result = evaluate(assumptions)
    e = result.economics
    # 3,000 orders, EUR 20 baskets, EUR 2 fee; independently calculated totals.
    expected = {
        "monthly_fulfilled_orders": "3000",
        "product_revenue": "60000",
        "delivery_revenue": "6000",
        "total_revenue": "66000",
        "product_cogs": "42000",
        "product_gross_profit": "18000",
        "product_gross_margin": "0.30",
        "shrinkage_cost": "600",
        "variable_fulfilment_cost": "1500",
        "variable_delivery_cost": "3000",
        "payment_cost": "1620",
        "acquisition_cost": "3000",
        "contribution": "14280",
        "contribution_per_order": "4.76",
        "fulfilment_payroll": "3000",
        "rider_payroll": "15000",
        "total_delivery_cost": "18000",
        "fixed_operating_costs": "19300",
        "total_operating_costs": "71020",
        "operating_profit": "-5020",
    }
    for metric, expected_value in expected.items():
        assert getattr(e, metric) == D(expected_value), metric
    assert e.cost_per_order == D(71020) / 3000
    assert e.contribution_margin == D(14280) / 66000
    assert e.operating_margin == -D(5020) / 66000
    assert not e.is_at_or_above_break_even
    assert result.cash.monthly_operating_burn == 5020
    assert result.cash.static_runway_months == 2


def test_zero_demand_preserves_payroll_and_fixed_costs(assumptions):
    result = evaluate(assumptions.with_changes(orders_per_day=0))
    e = result.economics
    assert e.total_revenue == e.product_cogs == e.contribution == 0
    assert e.operating_profit == -19300
    assert e.contribution_per_order == D("4.76")
    assert (
        e.cost_per_order
        is e.contribution_margin
        is e.product_gross_margin
        is e.operating_margin
        is None
    )
    assert result.capacity.required_riders == result.capacity.required_fulfilment_workers == 0


def test_zero_sales_value_has_undefined_margins(assumptions):
    result = evaluate(assumptions.with_changes(average_order_value=0, delivery_fee=0))
    assert result.economics.total_revenue == 0
    assert result.economics.contribution_margin is None
    assert result.economics.cost_per_order is not None


def test_capacity_limits_all_order_driven_revenue_and_expenses(assumptions):
    e = evaluate(assumptions.with_changes(orders_per_day=300)).economics
    assert e.monthly_fulfilled_orders == 6000
    assert e.total_revenue == 132000
    assert e.product_cogs == 84000
    assert e.payment_cost == 3240
    assert e.acquisition_cost == 6000
    assert e.fixed_operating_costs == 19300


@pytest.mark.parametrize("stockout", ["0", "0.5", "1"])
@pytest.mark.parametrize("demand", [0, 10, 100, 200, 1000])
def test_accounting_and_demand_conservation(assumptions, stockout, demand):
    result = evaluate(assumptions.with_changes(orders_per_day=demand, stockout_rate=stockout))
    e, c = result.economics, result.capacity
    assert e.total_revenue - e.total_operating_costs == e.operating_profit
    assert e.contribution - e.fixed_operating_costs == e.operating_profit
    assert (
        c.fulfilled_orders_per_day + c.stockout_lost_orders_per_day + c.capacity_lost_orders_per_day
        == demand
    )
    assert 0 <= c.system_utilisation <= 1


def test_paid_labour_is_not_also_variable(assumptions):
    base = evaluate(assumptions).economics
    alternative = evaluate(assumptions.with_changes(worker_hourly_cost=20)).economics
    assert alternative.contribution_per_order == base.contribution_per_order
    assert alternative.operating_profit == base.operating_profit - 3000


def test_determinism_does_not_depend_on_callers_decimal_context():
    baseline = evaluate(Assumptions())
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        assert evaluate(Assumptions()) == baseline
