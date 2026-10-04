"""Transparent reporting allocations of existing outputs, not a second model."""

from decimal import Decimal

from app.domain.assumptions import Assumptions
from app.domain.results import CapacityResult, EconomicsResult, ReportingResult, ResourceGap

ALLOCATED_COMPONENTS = (
    "product_revenue",
    "delivery_revenue",
    "total_revenue",
    "product_cogs",
    "product_gross_profit",
    "shrinkage_cost",
    "variable_fulfilment_cost",
    "variable_delivery_cost",
    "payment_cost",
    "acquisition_cost",
    "contribution",
    "fulfilment_payroll",
    "rider_payroll",
    "fixed_operating_costs",
    "operating_profit",
)


def reporting(a: Assumptions, c: CapacityResult, e: EconomicsResult) -> ReportingResult:
    orders = e.monthly_fulfilled_orders
    capacities = {
        "fulfilment": c.fulfilment_capacity_per_day,
        "delivery": c.delivery_capacity_per_day,
        "store": c.store_capacity_per_day,
    }
    return ReportingResult(
        per_fulfilled_order={
            key: getattr(e, key) / orders if orders else None for key in ALLOCATED_COMPONENTS
        },
        resource_gaps={
            resource: ResourceGap(
                spare_after_fulfilment=max(Decimal(0), capacity - c.fulfilled_orders_per_day),
                shortfall_to_eligible_demand=max(Decimal(0), c.eligible_orders_per_day - capacity),
            )
            for resource, capacity in capacities.items()
        },
        additional_fulfilment_workers=max(0, c.required_fulfilment_workers - a.fulfilment_workers),
        additional_riders=max(0, c.required_riders - a.riders),
    )
