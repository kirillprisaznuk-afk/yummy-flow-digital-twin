"""Bounded local analysis requests; financial mathematics stays in analytics/domain."""

from threading import BoundedSemaphore

from fastapi import APIRouter, HTTPException

from app.analytics.contracts import (
    SensitivityRequest,
    SensitivityResult,
    SimulationRequest,
    SimulationResult,
    SimulationSettings,
)
from app.analytics.sensitivity import sensitivity
from app.analytics.simulation import simulate

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
simulation_slot = BoundedSemaphore(1)


@router.get("/defaults", response_model=SimulationSettings)
def defaults() -> SimulationSettings:
    return SimulationSettings()


@router.post("/sensitivity", response_model=SensitivityResult)
def analyse(payload: SensitivityRequest) -> SensitivityResult:
    return sensitivity(payload.assumptions)


@router.post("/simulation", response_model=SimulationResult)
def run_simulation(payload: SimulationRequest) -> SimulationResult:
    if not simulation_slot.acquire(blocking=False):
        raise HTTPException(429, "A simulation is already running. Please retry when it finishes.")
    try:
        return simulate(payload)
    finally:
        simulation_slot.release()
