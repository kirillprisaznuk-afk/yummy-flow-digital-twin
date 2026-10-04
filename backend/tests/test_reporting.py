from decimal import Decimal as D

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate


def test_allocations_and_resource_gaps_have_independent_expected_values():
    a = Assumptions().with_changes(
        orders_per_day="100",
        stockout_rate="0",
        average_order_value="20",
        gross_margin="0.3",
        delivery_fee="2",
        shrinkage_rate="0",
        variable_fulfilment_cost_per_order="1",
        variable_delivery_cost_per_order="2",
        payment_fee_rate="0",
        payment_fee_per_order="0",
        new_customer_order_share="0",
        store_orders_per_hour="5",
        operating_hours_per_day="10",
    )
    result = evaluate(a)
    r = result.reporting
    # Physical ceiling = 5 * 10 = 50/day; 1,500 monthly fulfilled orders.
    assert r.per_fulfilled_order["product_revenue"] == 20
    assert r.per_fulfilled_order["delivery_revenue"] == 2
    assert r.per_fulfilled_order["product_cogs"] == 14
    assert r.per_fulfilled_order["product_gross_profit"] == 6
    assert r.per_fulfilled_order["contribution"] == 5
    assert r.per_fulfilled_order["fixed_operating_costs"] == D(109660) / 1500
    assert r.resource_gaps["store"].spare_after_fulfilment == 0
    assert r.resource_gaps["store"].shortfall_to_eligible_demand == 50
    assert r.additional_fulfilment_workers == 0
    assert r.additional_riders == 0


def test_zero_volume_has_no_per_order_allocation_and_stockouts_are_not_capacity_loss():
    r = evaluate(Assumptions().with_changes(stockout_rate="1")).reporting
    assert all(value is None for value in r.per_fulfilled_order.values())
    assert all(gap.shortfall_to_eligible_demand == 0 for gap in r.resource_gaps.values())
    assert r.additional_fulfilment_workers == 0
    assert r.additional_riders == 0


def test_zero_staff_has_a_real_resource_requirement_not_an_infinite_ratio():
    result = evaluate(Assumptions().with_changes(fulfilment_workers=0, riders=0))
    assert result.reporting.additional_fulfilment_workers == 11
    assert result.reporting.additional_riders == 38
    assert result.reporting.resource_gaps["delivery"].shortfall_to_eligible_demand == 686
