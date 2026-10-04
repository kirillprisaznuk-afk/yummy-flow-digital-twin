from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.main import create_app
from app.models.scenario import Scenario


@pytest.fixture
def client(database_url):
    with TestClient(create_app(database_url)) as client:
        yield client


def test_defaults_health_and_openapi_contract(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/defaults").json() == Assumptions().model_dump(mode="json")
    schema = client.get("/openapi.json").json()
    assert "/api/v1/evaluate" in schema["paths"]
    assert "/api/v1/scenarios/{scenario_id}" in schema["paths"]
    assert client.get("/docs").status_code == 200


def test_evaluate_delegates_to_domain_with_exact_decimal_values(client, assumptions):
    response = client.post("/api/v1/evaluate", json=assumptions.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json() == evaluate(assumptions).model_dump(mode="json")
    assert isinstance(response.json()["economics"]["operating_profit"], str)
    assert Decimal(response.json()["economics"]["operating_profit"]) == -5020


@pytest.mark.parametrize(
    "inputs",
    [
        {"orders_per_day": -1},
        {"gross_margin": 20},
        {"riders": 1.5},
        {"starting_cash": "NaN"},
        {"worker_hourly_cost": "Infinity"},
        {"orders_per_day": "0.0000001"},
        {"orders_per_day": "1e-999999"},
        {"extra": "not allowed"},
        {"riders": True},
    ],
)
def test_invalid_inputs_have_useful_422_responses(client, inputs):
    response = client.post("/api/v1/evaluate", json=inputs)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][0] == "body"


def test_nonstandard_nan_json_is_rejected_without_server_error(client):
    response = client.post(
        "/api/v1/evaluate",
        content='{"orders_per_day": NaN}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422


def test_comparison_endpoint_preserves_capacity_ceiling(client, assumptions):
    response = client.post(
        "/api/v1/compare",
        json={
            "baseline": assumptions.with_changes(orders_per_day=300).model_dump(mode="json"),
            "alternative": assumptions.with_changes(orders_per_day=390).model_dump(mode="json"),
        },
    )
    assert response.status_code == 200
    assert Decimal(response.json()["deltas"]["total_revenue"]["absolute_change"]) == 0


def test_scenario_create_read_update_evaluate_delete_round_trip(client, assumptions):
    payload = {"name": " Baseline ", "assumptions": assumptions.model_dump(mode="json")}
    created = client.post("/api/v1/scenarios", json=payload)
    assert created.status_code == 201
    record = created.json()
    path = f"/api/v1/scenarios/{record['id']}"
    assert record["name"] == "Baseline"
    assert record["model_version"] == "1.1"
    assert record["data_classification"] == "illustrative_synthetic"
    assert record["created_at"].endswith("Z")
    assert client.get(path).json() == record
    assert client.get("/api/v1/scenarios").json() == [record]
    saved = client.get(f"{path}/evaluation").json()
    assert saved["scenario"] == record
    assert saved["evaluation"] == evaluate(assumptions).model_dump(mode="json")
    updated_assumptions = assumptions.with_changes(
        orders_per_day=200, average_order_value="20.123456"
    )
    replaced = client.put(
        path,
        json={
            "name": "Growth",
            "description": "More demand and a precise basket value",
            "assumptions": updated_assumptions.model_dump(mode="json"),
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["id"] == record["id"]
    assert replaced.json()["created_at"] == record["created_at"]
    assert replaced.json()["updated_at"] >= record["updated_at"]
    assert client.get(path).json()["assumptions"]["average_order_value"] == "20.123456"
    assert client.get(f"{path}/evaluation").json()["evaluation"] == evaluate(
        updated_assumptions
    ).model_dump(mode="json")
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.get("/api/v1/scenarios").json() == []


def test_bad_update_does_not_change_stored_scenario(client):
    before = client.post("/api/v1/scenarios", json={"name": "Baseline"}).json()
    path = f"/api/v1/scenarios/{before['id']}"
    assert (
        client.put(path, json={"name": " ", "assumptions": {"gross_margin": -1}}).status_code == 422
    )
    assert client.get(path).json() == before


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_unknown_scenario_returns_404(client, method):
    kwargs = (
        {"json": {"name": "Updated", "assumptions": Assumptions().model_dump(mode="json")}}
        if method == "put"
        else {}
    )
    response = getattr(client, method)(f"/api/v1/scenarios/{uuid4()}", **kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "Scenario not found"


def test_pagination_and_identifier_validation(client):
    for name in ["Baseline", "Alternative"]:
        client.post("/api/v1/scenarios", json={"name": name})
    assert client.get("/api/v1/scenarios?limit=1").json()[0]["name"] == "Alternative"
    assert client.get("/api/v1/scenarios?limit=1&offset=1").json()[0]["name"] == "Baseline"
    assert client.get("/api/v1/scenarios?limit=101").status_code == 422
    assert client.get("/api/v1/scenarios?offset=-1").status_code == 422
    assert client.get("/api/v1/scenarios/not-a-uuid").status_code == 422


@pytest.mark.parametrize("name", ["", "   ", "x" * 121])
def test_invalid_scenario_name_is_rejected(client, name):
    assert client.post("/api/v1/scenarios", json={"name": name}).status_code == 422


@pytest.mark.parametrize("stored_version", ["1.0", "future-version"])
def test_unsupported_stored_model_version_is_not_silently_reinterpreted(client, stored_version):
    record = client.post("/api/v1/scenarios", json={"name": "Future model"}).json()
    with client.app.state.database.sessions() as session:
        row = session.get(Scenario, UUID(record["id"]))
        row.model_version = stored_version
        session.commit()
    path = f"/api/v1/scenarios/{record['id']}"
    assert client.get(f"{path}/evaluation").status_code == 409
    assert client.get(path).json()["model_version"] == stored_version
    assert (
        client.put(
            path, json={"name": "Overwrite", "assumptions": record["assumptions"]}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Rename only"},
        {"name": "Partial", "assumptions": {}},
        {"name": "Partial", "assumptions": {"orders_per_day": 1}},
    ],
)
def test_replacement_cannot_silently_reset_assumptions(client, payload):
    record = client.post(
        "/api/v1/scenarios", json={"name": "Baseline", "assumptions": {"monthly_rent": "4321"}}
    ).json()
    path = f"/api/v1/scenarios/{record['id']}"
    assert client.put(path, json=payload).status_code == 422
    assert client.get(path).json() == record


@pytest.mark.parametrize("corruption", ["missing_field", "invalid_value"])
def test_bad_stored_snapshots_do_not_silently_acquire_defaults(client, corruption):
    record = client.post("/api/v1/scenarios", json={"name": "Baseline"}).json()
    with client.app.state.database.sessions() as session:
        row = session.get(Scenario, UUID(record["id"]))
        values = dict(row.assumptions)
        if corruption == "missing_field":
            del values["monthly_rent"]
        else:
            values["gross_margin"] = "2"
        row.assumptions = values
        session.commit()
    assert client.get(f"/api/v1/scenarios/{record['id']}/evaluation").status_code == 409


def test_database_failures_do_not_expose_credentials_or_sql(client, monkeypatch):
    def fail(*args, **kwargs):
        raise OperationalError("sensitive statement", {}, Exception("secret-password"))

    monkeypatch.setattr("app.services.scenarios.create_scenario", fail)
    response = client.post("/api/v1/scenarios", json={"name": "Baseline"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Scenario storage is unavailable"}


def test_real_database_failure_returns_503_and_next_session_can_recover(client):
    database = client.app.state.database
    # This client's isolated temporary database is disposable.
    Scenario.__table__.drop(database.engine)
    failed = client.post("/api/v1/scenarios", json={"name": "Unavailable"})
    assert failed.status_code == 503
    Scenario.__table__.create(database.engine)
    response = client.post("/api/v1/scenarios", json={"name": "Recovered"})
    assert response.status_code == 201
    assert [row["name"] for row in client.get("/api/v1/scenarios").json()] == ["Recovered"]
