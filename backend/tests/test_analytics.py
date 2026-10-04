from decimal import Decimal as D
from random import Random

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.analytics.contracts import SimulationRequest, SimulationSettings, Uncertainty
from app.analytics.sensitivity import sensitivity
from app.analytics.simulation import (
    draw_assumptions,
    histogram,
    percentile,
    sampling_bounds,
    simulate,
)
from app.api.analytics import simulation_slot
from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.main import create_app


def zero_uncertainty():
    return Uncertainty(**dict.fromkeys(Uncertainty.model_fields, D(0)))


def test_sensitivity_independent_arithmetic_ranking_and_input_isolation(assumptions):
    before = assumptions.model_dump()
    result = sensitivity(assumptions)
    rows = {v.key: v for v in result.variables}
    assert assumptions.model_dump() == before
    assert result.baseline.economics.operating_profit == -5020
    assert result.variables[0].key == "gross_margin"
    assert rows["gross_margin"].impact_range == 7200
    assert rows["average_order_value"].impact_range == 6480
    assert rows["monthly_rent"].impact_range == 400
    assert rows["worker_hourly_cost"].impact_range == 1200
    assert [p.value for p in rows["gross_margin"].points] == list(
        map(D, [".24", ".27", ".30", ".33", ".36"])
    )
    assert rows["orders_per_day"].points[-1].result.economics.operating_profit == -2164
    assert all(v.points[2].result == result.baseline for v in result.variables)
    assert all(
        a.impact_range >= b.impact_range
        for a, b in zip(result.variables, result.variables[1:], strict=False)
    )


def test_sensitivity_capacity_plateau_and_invalid_points_are_not_clipped():
    result = sensitivity(Assumptions().with_changes(gross_margin=".95"))
    rows = {v.key: v for v in result.variables}
    assert rows["orders_per_day"].points[-1].operating_profit_delta == 0
    assert rows["gross_margin"].points[-1].value == D("1.14")
    assert rows["gross_margin"].points[-1].result is None
    assert rows["gross_margin"].points[-1].unavailable_reason
    assert rows["gross_margin"].points[0].result is not None


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"orders_per_day": "0"},
        {"stockout_rate": "1"},
        {"picking_minutes_per_order": "7", "fulfilment_workers": 1},
    ],
)
def test_zero_uncertainty_exactly_reproduces_deterministic_model(changes):
    a = Assumptions().with_changes(**changes)
    result = simulate(
        SimulationRequest(
            assumptions=a, settings=SimulationSettings(uncertainty=zero_uncertainty())
        )
    )
    baseline = evaluate(a)
    assert result.expected_operating_profit == baseline.economics.operating_profit
    assert result.p10 == result.p50 == result.p90 == baseline.economics.operating_profit
    assert result.expected_fulfilled_orders_per_day == baseline.capacity.fulfilled_orders_per_day
    assert (
        result.expected_capacity_lost_orders_per_day
        == baseline.capacity.capacity_lost_orders_per_day
    )
    assert sum(b.count for b in result.histogram) == result.runs == 1000
    assert len(result.histogram) == 1


def test_seed_reproduction_changes_and_probability_conservation():
    request = SimulationRequest(assumptions=Assumptions())
    result = simulate(request)
    assert result == simulate(request)
    changed = simulate(
        SimulationRequest(assumptions=request.assumptions, settings=SimulationSettings(seed=43))
    )
    assert changed.sample_digest != result.sample_digest
    assert changed.expected_operating_profit != result.expected_operating_profit
    assert result.p10 <= result.p50 <= result.p90
    assert result.probability_profit + result.probability_loss + result.probability_break_even == 1
    assert 0 <= result.probability_capacity_constraint <= 1
    assert all(0 <= v <= 1 for v in result.bottleneck_probabilities.values())
    assert sum(b.count for b in result.histogram) == 1000
    assert (
        result.expected_total_lost_orders_per_day
        == result.expected_capacity_lost_orders_per_day
        + result.expected_stockout_lost_orders_per_day
    )


def test_generated_seed_can_be_replayed():
    result = simulate(
        SimulationRequest(assumptions=Assumptions(), settings=SimulationSettings(seed=None))
    )
    replay = simulate(
        SimulationRequest(assumptions=Assumptions(), settings=SimulationSettings(seed=result.seed))
    )
    assert replay.sample_digest == result.sample_digest
    assert replay.histogram == result.histogram


@pytest.mark.parametrize("margin", ["0", ".001", ".999", "1"])
def test_samples_obey_physical_and_input_precision_bounds(margin):
    request = SimulationRequest(
        assumptions=Assumptions().with_changes(
            gross_margin=margin, orders_per_day="1000000000", average_order_value="0"
        ),
        settings=SimulationSettings(
            uncertainty=Uncertainty(**dict.fromkeys(Uncertainty.model_fields, D(100)))
        ),
    )
    bounds = sampling_bounds(request)
    rng = Random(123)
    for _ in range(200):
        sample = draw_assumptions(request.assumptions, bounds, rng)
        assert sample.average_order_value == 0
        assert 0 <= sample.gross_margin <= 1
        for key, bound in bounds.items():
            assert bound.low <= getattr(sample, key) <= bound.high


def test_capacity_is_enforced_in_all_draws_and_losses_are_distinct():
    settings = SimulationSettings(
        uncertainty=zero_uncertainty().model_copy(update={"orders_per_day": D(20)})
    )
    result = simulate(
        SimulationRequest(
            assumptions=Assumptions().with_changes(orders_per_day="1000"), settings=settings
        )
    )
    assert result.probability_capacity_constraint == 1
    assert result.expected_fulfilled_orders_per_day == D("652.8")
    assert result.expected_operating_profit == D("22731.7568")
    assert result.bottleneck_probabilities == {"fulfilment": 0, "delivery": 1, "store": 0}
    assert result.expected_capacity_lost_orders_per_day > 100
    assert result.expected_stockout_lost_orders_per_day > 0


def test_tied_zero_capacity_and_exact_break_even_are_not_profitable():
    a = Assumptions().with_changes(
        fulfilment_workers=0,
        riders=0,
        store_orders_per_hour="0",
        monthly_rent="0",
        monthly_utilities="0",
        monthly_software_admin="0",
    )
    result = simulate(SimulationRequest(assumptions=a))
    assert result.probability_profit == result.probability_loss == 0
    assert result.probability_break_even == result.probability_capacity_constraint == 1
    assert all(v == 1 for v in result.bottleneck_probabilities.values())


def test_percentiles_and_histogram_against_hand_values():
    values = list(map(D, [0, 10, 20, 30, 40]))
    assert [percentile(values, D(q)) for q in (".1", ".5", ".9")] == [4, 20, 36]
    bins = histogram(values)
    assert bins[0].lower == 0 and bins[-1].upper == 40
    assert bins[0].count == bins[-1].count == 1
    assert sum(b.count for b in bins) == 5


@pytest.mark.parametrize(
    "settings",
    [
        {"runs": 999},
        {"runs": 10001},
        {"runs": True},
        {"seed": -1},
        {"seed": 1.5},
        {"uncertainty": {"gross_margin": "NaN"}},
        {"uncertainty": {"orders_per_day": -1}},
        {"uncertainty": {"gross_margin": 101}},
        {"uncertainty": {"riders": 10}},
    ],
)
def test_invalid_analysis_settings_are_rejected(settings):
    with pytest.raises(ValidationError):
        SimulationSettings.model_validate(settings)


def test_analytics_api_contract_validation_and_busy_response(database_url):
    with TestClient(create_app(database_url)) as client:
        defaults = client.get("/api/v1/analytics/defaults")
        assert defaults.status_code == 200
        assert defaults.json()["runs"] == 1000
        payload = {"assumptions": Assumptions().model_dump(mode="json")}
        s = client.post("/api/v1/analytics/sensitivity", json=payload)
        assert s.status_code == 200 and len(s.json()["variables"]) == 6
        m = client.post("/api/v1/analytics/simulation", json=payload)
        assert m.status_code == 200 and m.json()["runs"] == 1000
        assert (
            client.post(
                "/api/v1/analytics/simulation", json=payload | {"settings": {"runs": 10001}}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/analytics/sensitivity", json={"assumptions": {"orders_per_day": -1}}
            ).status_code
            == 422
        )
        assert simulation_slot.acquire(blocking=False)
        try:
            busy = client.post("/api/v1/analytics/simulation", json=payload)
            assert busy.status_code == 429
        finally:
            simulation_slot.release()
