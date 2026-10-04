"""Independent monthly assumption draws; no invented daily cash paths."""

import hashlib
import platform
import random
import secrets
from decimal import Decimal
from fractions import Fraction

from app.analytics.contracts import (
    HistogramBin,
    SamplingBounds,
    SimulationRequest,
    SimulationResult,
)
from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.domain.precision import as_decimal, calculation

QUANTUM = Decimal("0.000001")


def sampling_bounds(request: SimulationRequest) -> dict[str, SamplingBounds]:
    bounds = {}
    for key, width in request.settings.uncertainty.model_dump().items():
        mode = getattr(request.assumptions, key)
        radius = width / 100 if key == "gross_margin" else mode * width / 100
        ceiling = Decimal(1) if key == "gross_margin" else Decimal(1_000_000_000)
        low, high = max(Decimal(0), mode - radius), min(ceiling, mode + radius)
        bounds[key] = SamplingBounds(
            low=low.quantize(QUANTUM),
            mode=mode,
            high=high.quantize(QUANTUM),
            bounded=low != mode - radius or high != mode + radius,
        )
    return bounds


def draw_assumptions(a: Assumptions, bounds: dict[str, SamplingBounds], rng: random.Random):
    changes = {}
    for key, b in bounds.items():
        value = (
            b.mode
            if b.low == b.high
            else Decimal(str(rng.triangular(float(b.low), float(b.high), float(b.mode))))
        )
        # Round to the model's accepted input resolution, then validate every draw.
        changes[key] = min(b.high, max(b.low, value.quantize(QUANTUM)))
    return a.with_changes(**changes)


def percentile(sorted_values: list[Decimal], fraction: Decimal) -> Decimal:
    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def histogram(values: list[Decimal]) -> list[HistogramBin]:
    low, high = min(values), max(values)
    if low == high:
        return [HistogramBin(lower=low, upper=high, count=len(values))]
    width = (high - low) / 24
    counts = [0] * 24
    for value in values:
        counts[min(23, int((value - low) / width))] += 1
    return [
        HistogramBin(
            lower=low + i * width, upper=high if i == 23 else low + (i + 1) * width, count=count
        )
        for i, count in enumerate(counts)
    ]


@calculation
def simulate(request: SimulationRequest) -> SimulationResult:
    request = SimulationRequest.model_validate(request.model_dump())
    a, settings = request.assumptions, request.settings
    seed = settings.seed if settings.seed is not None else secrets.randbits(32)
    rng = random.Random(seed)
    bounds = sampling_bounds(request)
    baseline = evaluate(a)
    profits = []
    fulfilled = capacity_lost = stockout_lost = Fraction(0)
    constrained = positive = negative = 0
    bottlenecks = dict.fromkeys(("fulfilment", "delivery", "store"), 0)
    digest = hashlib.sha256()
    for _ in range(settings.runs):
        sampled = draw_assumptions(a, bounds, rng)
        result = evaluate(sampled)
        profit, c = result.economics.operating_profit, result.capacity
        profits.append(profit)
        positive += profit > 0
        negative += profit < 0
        constrained += bool(c.active_bottlenecks)
        for key in c.active_bottlenecks:
            bottlenecks[key] += 1
        fulfilled += Fraction(c.fulfilled_orders_per_day)
        capacity_lost += Fraction(c.capacity_lost_orders_per_day)
        stockout_lost += Fraction(c.stockout_lost_orders_per_day)
        digest.update((sampled.model_dump_json() + "\n").encode())
    n = Decimal(settings.runs)
    ordered = sorted(profits)
    p10, p50, p90 = (percentile(ordered, Decimal(q)) for q in ("0.1", "0.5", "0.9"))
    expected = as_decimal(sum(map(Fraction, profits), Fraction(0)) / settings.runs)
    fulfilled = as_decimal(fulfilled / settings.runs)
    capacity_lost = as_decimal(capacity_lost / settings.runs)
    stockout_lost = as_decimal(stockout_lost / settings.runs)
    return SimulationResult(
        model_version=baseline.model_version,
        python_version=platform.python_version(),
        runs=settings.runs,
        seed=seed,
        settings=settings,
        baseline=baseline,
        bounds=bounds,
        expected_operating_profit=expected,
        p10=p10,
        p50=p50,
        p90=p90,
        probability_profit=positive / n,
        probability_loss=negative / n,
        probability_break_even=(settings.runs - positive - negative) / n,
        probability_capacity_constraint=constrained / n,
        bottleneck_probabilities={key: value / n for key, value in bottlenecks.items()},
        expected_fulfilled_orders_per_day=fulfilled,
        expected_capacity_lost_orders_per_day=capacity_lost,
        expected_stockout_lost_orders_per_day=stockout_lost,
        expected_total_lost_orders_per_day=capacity_lost + stockout_lost,
        histogram=histogram(profits),
        sample_digest=digest.hexdigest(),
        insights=[
            f"Operating profit is positive in {positive / n:.1%} of draws under these assumptions.",
            f"Capacity constrains eligible demand in {constrained / n:.1%} of draws; "
            f"expected capacity loss is {capacity_lost:.1f} orders/day.",
            f"Downside P10 is EUR {p10:,.0f}/month; it is a percentile, not a worst case.",
            "These are independent hypothetical monthly states, not a forecast. "
            "No cash-depletion probability is estimated from static runway.",
        ],
    )
