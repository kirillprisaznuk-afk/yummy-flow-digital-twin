from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.assumptions import Assumptions
from app.domain.results import Evaluation


class ScenarioWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    assumptions: Assumptions = Field(default_factory=Assumptions)


class ScenarioRead(ScenarioWrite):
    assumptions: Assumptions
    id: UUID
    model_version: str = Field(min_length=1, max_length=20)
    data_classification: Literal["illustrative_synthetic"] = "illustrative_synthetic"
    created_at: datetime
    updated_at: datetime


class ScenarioReplace(ScenarioWrite):
    assumptions: Assumptions

    @field_validator("assumptions")
    @classmethod
    def require_full_snapshot(cls, value: Assumptions) -> Assumptions:
        missing = set(Assumptions.model_fields) - value.model_fields_set
        if missing:
            raise ValueError(
                "Replacement requires all assumption fields; missing: " + ", ".join(sorted(missing))
            )
        return value


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline: Assumptions
    alternative: Assumptions


class SavedEvaluation(BaseModel):
    scenario: ScenarioRead
    evaluation: Evaluation
