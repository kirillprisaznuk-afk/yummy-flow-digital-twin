"""Scenario persistence and explicit version compatibility checks."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate
from app.domain.version import MODEL_VERSION
from app.models.scenario import Scenario
from app.schemas.scenario import SavedEvaluation, ScenarioRead, ScenarioReplace, ScenarioWrite


class ScenarioNotFoundError(Exception):
    pass


class UnsupportedModelVersionError(Exception):
    pass


class InvalidStoredScenarioError(Exception):
    pass


def _record(row: Scenario) -> ScenarioRead:
    # Missing saved values must not silently turn into today's default assumptions.
    if not isinstance(row.assumptions, dict) or set(row.assumptions) != set(
        Assumptions.model_fields
    ):
        raise InvalidStoredScenarioError(
            "Saved scenario has an incomplete or incompatible snapshot"
        )
    try:
        assumptions = Assumptions.model_validate(row.assumptions)
    except ValidationError as exc:
        raise InvalidStoredScenarioError("Saved scenario contains invalid assumptions") from exc
    return ScenarioRead(
        id=row.id,
        name=row.name,
        description=row.description,
        assumptions=assumptions,
        model_version=row.model_version,
        created_at=row.created_at.replace(tzinfo=UTC)
        if row.created_at.tzinfo is None
        else row.created_at,
        updated_at=row.updated_at.replace(tzinfo=UTC)
        if row.updated_at.tzinfo is None
        else row.updated_at,
    )


def _find(session: Session, scenario_id: UUID) -> Scenario:
    row = session.get(Scenario, scenario_id)
    if row is None:
        raise ScenarioNotFoundError("Scenario not found")
    return row


def create_scenario(session: Session, payload: ScenarioWrite) -> ScenarioRead:
    row = Scenario(
        name=payload.name,
        description=payload.description,
        assumptions=payload.assumptions.model_dump(mode="json"),
    )
    session.add(row)
    session.commit()
    return _record(row)


def get_scenario(session: Session, scenario_id: UUID) -> ScenarioRead:
    return _record(_find(session, scenario_id))


def list_scenarios(session: Session, limit: int, offset: int) -> list[ScenarioRead]:
    query = (
        select(Scenario)
        .order_by(Scenario.created_at.desc(), Scenario.id)
        .limit(limit)
        .offset(offset)
    )
    return [_record(row) for row in session.scalars(query)]


def replace_scenario(session: Session, scenario_id: UUID, payload: ScenarioReplace) -> ScenarioRead:
    row = _find(session, scenario_id)
    if row.model_version != MODEL_VERSION:
        raise UnsupportedModelVersionError("Saved scenario uses an unsupported model version")
    _record(row)  # Validate the existing snapshot before replacement.
    row.name = payload.name
    row.description = payload.description
    row.assumptions = payload.assumptions.model_dump(mode="json")
    row.updated_at = datetime.now(UTC)
    session.commit()
    return _record(row)


def delete_scenario(session: Session, scenario_id: UUID) -> None:
    session.delete(_find(session, scenario_id))
    session.commit()


def evaluate_scenario(session: Session, scenario_id: UUID) -> SavedEvaluation:
    scenario = get_scenario(session, scenario_id)
    if scenario.model_version != MODEL_VERSION:
        raise UnsupportedModelVersionError("Saved scenario uses an unsupported model version")
    return SavedEvaluation(scenario=scenario, evaluation=evaluate(scenario.assumptions))
