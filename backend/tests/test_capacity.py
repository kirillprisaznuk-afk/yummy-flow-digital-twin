from decimal import Decimal as D

import pytest

from app.domain.capacity import calculate_capacity


def test_hand_calculated_capacity_and_staffing(assumptions):
    c = calculate_capacity(assumptions)
    assert (
        c.fulfilment_capacity_per_day
        == c.delivery_capacity_per_day
        == c.store_capacity_per_day
        == 200
    )
    assert c.limiting_resources == ("fulfilment", "delivery", "store")
    assert c.active_bottlenecks == ()
    assert c.system_utilisation == D("0.5")
    assert c.required_fulfilment_workers == 1
    assert c.required_riders == 5
    assert c.delivery_cycle_minutes == 15
    assert c.deliveries_per_productive_rider_hour == 4
    assert c.orders_per_productive_worker_hour == 20
    assert "fits" in c.explanation


@pytest.mark.parametrize(
    "changes,resource",
    [
        ({"fulfilment_workers": 1}, "fulfilment"),
        ({"riders": 5}, "delivery"),
        ({"store_orders_per_hour": 10}, "store"),
    ],
)
def test_each_resource_can_become_active_bottleneck(assumptions, changes, resource):
    c = calculate_capacity(assumptions.with_changes(orders_per_day=150, **changes))
    assert c.active_bottlenecks == (resource,)
    assert c.fulfilled_orders_per_day == 100
    assert c.capacity_lost_orders_per_day == 50
    assert "50.00" in c.explanation


def test_ties_and_exact_capacity_are_explicit(assumptions):
    assert calculate_capacity(assumptions.with_changes(orders_per_day=200)).active_bottlenecks == ()
    c = calculate_capacity(assumptions.with_changes(orders_per_day=201))
    assert c.active_bottlenecks == ("fulfilment", "delivery", "store")
    assert c.required_fulfilment_workers == 3
    assert c.required_riders == 11


@pytest.mark.parametrize(
    "field,utilisation",
    [
        ("riders", "delivery_utilisation"),
        ("fulfilment_workers", "fulfilment_utilisation"),
        ("store_orders_per_hour", "store_utilisation"),
    ],
)
def test_zero_resource_has_no_capacity_and_no_undefined_division(assumptions, field, utilisation):
    c = calculate_capacity(assumptions.with_changes(**{field: 0}))
    assert c.fulfilled_orders_per_day == 0
    assert c.system_utilisation is None
    assert getattr(c, utilisation) is None
    assert c.capacity_lost_orders_per_day == 100


def test_distance_lowers_rider_capacity(assumptions):
    c = calculate_capacity(assumptions.with_changes(average_delivery_distance_km=2))
    assert c.delivery_cycle_minutes == 25
    assert c.delivery_capacity_per_day == 120
    assert c.required_riders == 9


def test_stockouts_are_applied_before_capacity(assumptions):
    c = calculate_capacity(assumptions.with_changes(orders_per_day=300, stockout_rate="0.2"))
    assert c.stockout_lost_orders_per_day == 60
    assert c.eligible_orders_per_day == 240
    assert c.fulfilled_orders_per_day == 200
    assert c.capacity_lost_orders_per_day == 40


def test_productivity_reduces_capacity_but_not_paid_hours(assumptions):
    c = calculate_capacity(assumptions.with_changes(worker_productive_fraction="0.25"))
    assert c.fulfilment_capacity_per_day == 50
    assert c.required_fulfilment_workers == 4


def test_paid_hours_outside_opening_window_cannot_create_capacity(assumptions):
    c = calculate_capacity(assumptions.with_changes(operating_hours_per_day=1))
    assert c.fulfilment_capacity_per_day == 40
    assert c.delivery_capacity_per_day == 40
    assert c.store_capacity_per_day == 20
    assert c.required_fulfilment_workers == 5
    assert c.required_riders == 25
