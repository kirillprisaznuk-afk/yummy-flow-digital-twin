"""Validated analysis settings and explicit, versioned reporting contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.assumptions import Assumptions, FiniteDecimal
from app.domain.results import Evaluation, Resource

ANALYTICS_VERSION = "1.0"
Width = Annotated[FiniteDecimal, Field(ge=0, le=100)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class Uncertainty(Contract):
    orders_per_day: Width = Decimal("15")
    average_order_value: Width = Decimal("8")
    gross_margin: Width = Decimal("3")
    variable_delivery_cost_per_order: Width = Decimal("10")
    variable_fulfilment_cost_per_order: Width = Decimal("10")


class SimulationSettings(Contract):
    runs: Annotated[int, Field(ge=1000, le=10000, strict=True)] = 1000
    seed: Annotated[int, Field(ge=0, le=4294967295, strict=True)] | None = 42
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)


class SensitivityRequest(Contract):
    assumptions: Assumptions


class SimulationRequest(SensitivityRequest):
    settings: SimulationSettings = Field(default_factory=SimulationSettings)


class SensitivityPoint(Contract):
    change_percent: int
    value: Decimal
    result: Evaluation | None
    operating_profit_delta: Decimal | None
    unavailable_reason: str | None = None


class SensitivityVariable(Contract):
    key: str
    label: str
    unit: str
    baseline_value: Decimal
    points: list[SensitivityPoint]
    impact_range: Decimal
    downside_delta: Decimal
    upside_delta: Decimal


class SensitivityResult(Contract):
    analytics_version: str = ANALYTICS_VERSION
    baseline: Evaluation
    variables: list[SensitivityVariable]
    insights: list[str]


class SamplingBounds(Contract):
    low: Decimal
    mode: Decimal
    high: Decimal
    bounded: bool


class HistogramBin(Contract):
    lower: Decimal
    upper: Decimal
    count: int


class SimulationResult(Contract):
    analytics_version: str = ANALYTICS_VERSION
    model_version: str
    python_version: str
    distribution: Literal["independent_triangular"] = "independent_triangular"
    runs: int
    seed: int
    settings: SimulationSettings
    baseline: Evaluation
    bounds: dict[str, SamplingBounds]
    expected_operating_profit: Decimal
    p10: Decimal
    p50: Decimal
    p90: Decimal
    probability_profit: Decimal
    probability_loss: Decimal
    probability_break_even: Decimal
    probability_capacity_constraint: Decimal
    bottleneck_probabilities: dict[Resource, Decimal]
    expected_fulfilled_orders_per_day: Decimal
    expected_capacity_lost_orders_per_day: Decimal
    expected_stockout_lost_orders_per_day: Decimal
    expected_total_lost_orders_per_day: Decimal
    histogram: list[HistogramBin]
    sample_digest: str
    insights: list[str]
