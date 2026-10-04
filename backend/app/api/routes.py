from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.domain.assumptions import Assumptions
from app.domain.comparison import compare
from app.domain.evaluation import evaluate
from app.domain.results import Comparison, Evaluation
from app.schemas.scenario import (
    ComparisonRequest,
    SavedEvaluation,
    ScenarioRead,
    ScenarioReplace,
    ScenarioWrite,
)
from app.services import scenarios

router = APIRouter(prefix="/api/v1")


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.database.sessions() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("/defaults", response_model=Assumptions, tags=["model"])
def defaults() -> Assumptions:
    return Assumptions()


@router.post("/evaluate", response_model=Evaluation, tags=["model"])
def evaluate_assumptions(assumptions: Assumptions) -> Evaluation:
    return evaluate(assumptions)


@router.post("/compare", response_model=Comparison, tags=["model"])
def compare_assumptions(payload: ComparisonRequest) -> Comparison:
    return compare(payload.baseline, payload.alternative)


@router.post("/scenarios", response_model=ScenarioRead, status_code=201, tags=["scenarios"])
def create(payload: ScenarioWrite, session: DatabaseSession) -> ScenarioRead:
    return scenarios.create_scenario(session, payload)


@router.get("/scenarios", response_model=list[ScenarioRead], tags=["scenarios"])
def list_saved(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ScenarioRead]:
    return scenarios.list_scenarios(session, limit, offset)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioRead, tags=["scenarios"])
def get_saved(scenario_id: UUID, session: DatabaseSession) -> ScenarioRead:
    return scenarios.get_scenario(session, scenario_id)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioRead, tags=["scenarios"])
def replace(scenario_id: UUID, payload: ScenarioReplace, session: DatabaseSession) -> ScenarioRead:
    return scenarios.replace_scenario(session, scenario_id, payload)


@router.delete("/scenarios/{scenario_id}", status_code=204, tags=["scenarios"])
def delete(scenario_id: UUID, session: DatabaseSession) -> Response:
    scenarios.delete_scenario(session, scenario_id)
    return Response(status_code=204)


@router.get(
    "/scenarios/{scenario_id}/evaluation", response_model=SavedEvaluation, tags=["scenarios"]
)
def evaluate_saved(scenario_id: UUID, session: DatabaseSession) -> SavedEvaluation:
    return scenarios.evaluate_scenario(session, scenario_id)
