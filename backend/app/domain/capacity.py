"""Average-day throughput, retaining exact ratios until output conversion."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil

from app.domain.assumptions import Assumptions
from app.domain.precision import as_decimal, calculation
from app.domain.results import CapacityResult, Resource


@dataclass(frozen=True)
class CapacityState:
    limits: dict[Resource, Fraction]
    eligible: Fraction
    worker_minutes: Fraction
    rider_minutes: Fraction
    handling_minutes: Fraction
    cycle_minutes: Fraction

    @property
    def system_capacity(self) -> Fraction:
        return min(self.limits.values())

    @property
    def fulfilled(self) -> Fraction:
        return min(self.eligible, self.system_capacity)


def capacity_state(a: Assumptions) -> CapacityState:
    """Shared exact quantities for throughput, staffing, and economic thresholds."""
    a = Assumptions.model_validate(a)
    opening_hours = a.operating_days_per_month * Fraction(a.operating_hours_per_day)
    worker_minutes = (
        min(Fraction(a.worker_paid_hours_per_month), opening_hours)
        * Fraction(a.worker_productive_fraction)
        * 60
    )
    rider_minutes = (
        min(Fraction(a.rider_paid_hours_per_month), opening_hours)
        * Fraction(a.rider_productive_fraction)
        * 60
    )
    handling = Fraction(a.picking_minutes_per_order) + Fraction(a.packing_minutes_per_order)
    cycle = Fraction(a.delivery_handoff_minutes) + (
        120 * Fraction(a.average_delivery_distance_km) / Fraction(a.rider_average_speed_kmh)
    )
    return CapacityState(
        limits={
            "fulfilment": a.fulfilment_workers
            * worker_minutes
            / (handling * a.operating_days_per_month),
            "delivery": a.riders * rider_minutes / (cycle * a.operating_days_per_month),
            "store": Fraction(a.store_orders_per_hour) * Fraction(a.operating_hours_per_day),
        },
        eligible=Fraction(a.orders_per_day) * (1 - Fraction(a.stockout_rate)),
        worker_minutes=worker_minutes,
        rider_minutes=rider_minutes,
        handling_minutes=handling,
        cycle_minutes=cycle,
    )


@calculation
def calculate_capacity(a: Assumptions) -> CapacityResult:
    a = Assumptions.model_validate(a)
    state = capacity_state(a)
    capacity, eligible, fulfilled = state.system_capacity, state.eligible, state.fulfilled
    limiting = tuple(resource for resource, value in state.limits.items() if value == capacity)
    active = limiting if eligible > capacity else ()
    utilisation = {
        key: as_decimal(fulfilled / value) if value else None for key, value in state.limits.items()
    }
    explanation = (
        f"{', '.join(limiting)} limits system capacity to {as_decimal(capacity):.2f} orders/day; "
        f"eligible demand is {as_decimal(eligible):.2f} orders/day. "
        + (
            f"Capacity leaves {as_decimal(eligible - fulfilled):.2f} eligible orders/day unserved."
            if active
            else "Current eligible demand fits within average system capacity."
        )
    )
    return CapacityResult(
        requested_orders_per_day=a.orders_per_day,
        eligible_orders_per_day=as_decimal(eligible),
        stockout_lost_orders_per_day=as_decimal(Fraction(a.orders_per_day) - eligible),
        capacity_lost_orders_per_day=as_decimal(eligible - fulfilled),
        fulfilled_orders_per_day=as_decimal(fulfilled),
        fulfilment_capacity_per_day=as_decimal(state.limits["fulfilment"]),
        delivery_capacity_per_day=as_decimal(state.limits["delivery"]),
        store_capacity_per_day=as_decimal(state.limits["store"]),
        system_capacity_per_day=as_decimal(capacity),
        limiting_resources=limiting,
        active_bottlenecks=active,
        fulfilment_utilisation=utilisation["fulfilment"],
        delivery_utilisation=utilisation["delivery"],
        store_utilisation=utilisation["store"],
        system_utilisation=as_decimal(fulfilled / capacity) if capacity else None,
        required_fulfilment_workers=ceil(
            eligible * a.operating_days_per_month * state.handling_minutes / state.worker_minutes
        ),
        required_riders=ceil(
            eligible * a.operating_days_per_month * state.cycle_minutes / state.rider_minutes
        ),
        delivery_cycle_minutes=as_decimal(state.cycle_minutes),
        deliveries_per_productive_rider_hour=as_decimal(60 / state.cycle_minutes),
        orders_per_productive_worker_hour=as_decimal(60 / state.handling_minutes),
        explanation=explanation,
    )
