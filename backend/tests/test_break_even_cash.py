from decimal import Decimal as D

import pytest

from app.domain.evaluation import evaluate


def test_break_even_threshold_and_revenue(assumptions):
    b = evaluate(assumptions).break_even
    # Independently worked values, checked to six decimal places.
    assert b.monthly_fulfilled_orders.quantize(D("0.000001")) == D("4054.621849")
    assert b.fulfilled_orders_per_day.quantize(D("0.000001")) == D("135.154062")
    assert b.requested_orders_per_day.quantize(D("0.000001")) == D("135.154062")
    assert b.monthly_revenue.quantize(D("0.000001")) == D("89201.680672")
    assert b.reachable_at_current_capacity
    assert b.reason == "reachable"
    assert evaluate(assumptions.with_changes(orders_per_day=135)).economics.operating_profit < 0
    assert evaluate(assumptions.with_changes(orders_per_day=136)).economics.operating_profit > 0


def test_break_even_adjusts_required_demand_for_stockouts(assumptions):
    b = evaluate(assumptions.with_changes(stockout_rate="0.5")).break_even
    assert b.requested_orders_per_day.quantize(D("0.000001")) == D("270.308123")
    assert (
        evaluate(
            assumptions.with_changes(stockout_rate="0.5", orders_per_day=270)
        ).economics.operating_profit
        < 0
    )
    assert (
        evaluate(
            assumptions.with_changes(stockout_rate="0.5", orders_per_day=271)
        ).economics.operating_profit
        > 0
    )


def test_positive_contribution_does_not_guarantee_feasible_break_even(assumptions):
    b = evaluate(assumptions.with_changes(store_orders_per_hour=1)).break_even
    assert b.monthly_fulfilled_orders > 0
    assert not b.reachable_at_current_capacity
    assert b.reason == "capacity_shortfall"


@pytest.mark.parametrize("delivery_cost", ["5.76", "6"])
def test_zero_or_negative_contribution_has_no_volume_break_even(assumptions, delivery_cost):
    b = evaluate(
        assumptions.with_changes(variable_delivery_cost_per_order=delivery_cost)
    ).break_even
    assert b.reason == "nonpositive_contribution"
    assert (
        b.monthly_fulfilled_orders
        is b.fulfilled_orders_per_day
        is b.requested_orders_per_day
        is b.monthly_revenue
        is None
    )


def test_complete_stockouts_cannot_reach_positive_break_even(assumptions):
    result = evaluate(assumptions.with_changes(stockout_rate=1))
    assert result.economics.total_revenue == 0
    assert result.break_even.requested_orders_per_day is None
    assert result.break_even.reason == "all_demand_stocked_out"


def test_no_fixed_costs_has_zero_threshold_even_with_complete_stockouts(assumptions):
    result = evaluate(
        assumptions.with_changes(
            worker_hourly_cost=0,
            rider_hourly_cost=0,
            monthly_rent=0,
            monthly_utilities=0,
            monthly_software_admin=0,
            stockout_rate=1,
        )
    )
    assert result.break_even.requested_orders_per_day == 0
    assert result.break_even.reachable_at_current_capacity
    assert result.economics.is_at_or_above_break_even


def test_exact_break_even_is_not_burning_cash(assumptions):
    result = evaluate(assumptions.with_changes(average_order_value=40, monthly_rent=12180))
    # Higher basket adds EUR 16,200 contribution, offset by EUR 11,180 additional rent.
    assert result.economics.operating_profit == 0
    assert result.economics.is_at_or_above_break_even
    assert result.cash.monthly_operating_burn == 0
    assert result.cash.static_runway_months is None


def test_profitable_operation_has_no_burn(assumptions):
    result = evaluate(assumptions.with_changes(orders_per_day=200, starting_cash=0))
    assert result.economics.operating_profit == 9260
    assert result.cash.runway_status == "no_operating_burn"
    assert result.cash.static_runway_months is None
    assert result.cash.cash_balance_is_zero


@pytest.mark.parametrize("cash,runway", [("0", "0"), ("5.02", "0.001"), ("10040", "2")])
def test_low_cash_runway(assumptions, cash, runway):
    result = evaluate(assumptions.with_changes(starting_cash=cash))
    assert result.cash.static_runway_months == D(runway)
    assert result.cash.runway_status == "burning_cash"
