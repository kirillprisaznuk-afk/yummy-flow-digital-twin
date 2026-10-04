"""Read-only result fields; undefined ratios use None, never infinity."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.domain.version import MODEL_VERSION, ModelVersion

Resource = Literal["fulfilment", "delivery", "store"]


class Result(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CapacityResult(Result):
    requested_orders_per_day: Decimal
    eligible_orders_per_day: Decimal
    stockout_lost_orders_per_day: Decimal
    capacity_lost_orders_per_day: Decimal
    fulfilled_orders_per_day: Decimal
    fulfilment_capacity_per_day: Decimal
    delivery_capacity_per_day: Decimal
    store_capacity_per_day: Decimal
    system_capacity_per_day: Decimal
    limiting_resources: tuple[Resource, ...]
    active_bottlenecks: tuple[Resource, ...]
    fulfilment_utilisation: Decimal | None
    delivery_utilisation: Decimal | None
    store_utilisation: Decimal | None
    system_utilisation: Decimal | None
    required_fulfilment_workers: int
    required_riders: int
    delivery_cycle_minutes: Decimal
    deliveries_per_productive_rider_hour: Decimal
    orders_per_productive_worker_hour: Decimal
    explanation: str


class EconomicsResult(Result):
    monthly_fulfilled_orders: Decimal
    product_revenue: Decimal
    delivery_revenue: Decimal
    total_revenue: Decimal
    product_cogs: Decimal
    product_gross_profit: Decimal
    product_gross_margin: Decimal | None
    shrinkage_cost: Decimal
    variable_fulfilment_cost: Decimal
    variable_delivery_cost: Decimal
    payment_cost: Decimal
    acquisition_cost: Decimal
    contribution: Decimal
    contribution_per_order: Decimal
    contribution_margin: Decimal | None
    fulfilment_payroll: Decimal
    rider_payroll: Decimal
    total_delivery_cost: Decimal
    fixed_operating_costs: Decimal
    total_operating_costs: Decimal
    cost_per_order: Decimal | None
    operating_profit: Decimal
    operating_margin: Decimal | None
    is_at_or_above_break_even: bool


class BreakEvenResult(Result):
    monthly_fulfilled_orders: Decimal | None
    fulfilled_orders_per_day: Decimal | None
    requested_orders_per_day: Decimal | None
    monthly_revenue: Decimal | None
    reachable_at_current_capacity: bool
    reason: Literal[
        "reachable",
        "capacity_shortfall",
        "all_demand_stocked_out",
        "nonpositive_contribution",
        "zero_fixed_costs",
    ]


class CashResult(Result):
    monthly_operating_burn: Decimal
    static_runway_months: Decimal | None
    runway_status: Literal["burning_cash", "no_operating_burn"]
    cash_balance_is_zero: bool


class ResourceGap(Result):
    spare_after_fulfilment: Decimal
    shortfall_to_eligible_demand: Decimal


class ReportingResult(Result):
    per_fulfilled_order: dict[str, Decimal | None]
    resource_gaps: dict[Resource, ResourceGap]
    additional_fulfilment_workers: int
    additional_riders: int


class Evaluation(Result):
    model_version: ModelVersion = MODEL_VERSION
    data_classification: Literal["illustrative_synthetic"] = "illustrative_synthetic"
    currency: Literal["EUR"] = "EUR"
    capacity: CapacityResult
    economics: EconomicsResult
    break_even: BreakEvenResult
    cash: CashResult
    reporting: ReportingResult


class MetricDelta(Result):
    baseline: Decimal | None
    alternative: Decimal | None
    absolute_change: Decimal | None
    relative_change: Decimal | None


class Comparison(Result):
    baseline_operating_days_per_month: int
    alternative_operating_days_per_month: int
    same_operating_days: bool
    baseline: Evaluation
    alternative: Evaluation
    deltas: dict[str, MetricDelta]
