"""Centralized synthetic defaults; none are observed Yummy Flow operating data."""

from collections.abc import Mapping
from decimal import Decimal
from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field

FiniteDecimal = Annotated[Decimal, Field(allow_inf_nan=False, max_digits=18, decimal_places=6)]
NonNegative = Annotated[FiniteDecimal, Field(ge=0, le=1_000_000_000)]
Positive = Annotated[FiniteDecimal, Field(gt=0, le=1_000_000_000)]
Fraction = Annotated[FiniteDecimal, Field(ge=0, le=1)]
Productivity = Annotated[FiniteDecimal, Field(gt=0, le=1)]
Headcount = Annotated[int, Field(ge=0, le=100_000, strict=True)]


class Assumptions(BaseModel):
    """One store, average operating day, VAT-exclusive EUR, fixed monthly staffing."""

    model_config = ConfigDict(
        frozen=True, extra="forbid", validate_default=True, revalidate_instances="always"
    )

    orders_per_day: NonNegative = Decimal("700")
    operating_days_per_month: Annotated[int, Field(ge=1, le=31, strict=True)] = 30
    operating_hours_per_day: Annotated[FiniteDecimal, Field(gt=0, le=24)] = Decimal("16")
    average_order_value: NonNegative = Decimal("28")
    delivery_fee: NonNegative = Decimal("1.99")
    gross_margin: Fraction = Decimal("0.25")
    shrinkage_rate: Fraction = Decimal("0.01")
    stockout_rate: Fraction = Decimal("0.02")
    variable_fulfilment_cost_per_order: NonNegative = Decimal("0.35")
    variable_delivery_cost_per_order: NonNegative = Decimal("0.50")
    payment_fee_rate: Fraction = Decimal("0.02")
    payment_fee_per_order: NonNegative = Decimal("0.10")
    customer_acquisition_cost: NonNegative = Decimal("8")
    new_customer_order_share: Fraction = Decimal("0.05")
    monthly_rent: NonNegative = Decimal("6500")
    monthly_utilities: NonNegative = Decimal("900")
    monthly_software_admin: NonNegative = Decimal("500")
    fulfilment_workers: Headcount = 12
    worker_paid_hours_per_month: Annotated[FiniteDecimal, Field(gt=0, le=240)] = Decimal("160")
    worker_hourly_cost: NonNegative = Decimal("14")
    worker_productive_fraction: Productivity = Decimal("0.85")
    picking_minutes_per_order: Positive = Decimal("3")
    packing_minutes_per_order: NonNegative = Decimal("1")
    store_orders_per_hour: NonNegative = Decimal("80")
    riders: Headcount = 36
    rider_paid_hours_per_month: Annotated[FiniteDecimal, Field(gt=0, le=240)] = Decimal("160")
    rider_hourly_cost: NonNegative = Decimal("13")
    rider_productive_fraction: Productivity = Decimal("0.85")
    average_delivery_distance_km: NonNegative = Decimal("1.5")
    rider_average_speed_kmh: Positive = Decimal("18")
    delivery_handoff_minutes: Positive = Decimal("5")
    starting_cash: NonNegative = Decimal("150000")

    def with_changes(self, **changes: object) -> Self:
        """Return a validated alternative without modifying this scenario."""
        return type(self).model_validate(self.model_dump() | changes)

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
        """Unlike Pydantic's default, copying may not bypass validation.

        All fields are immutable scalars, so deep and shallow copies are equivalent.
        """
        return self.with_changes(**(update or {}))
