from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class SimulationStatus(BaseModel):
    running: bool
    tick: int
    time: float
    agent_count: int
    alive_count: int


class WorldSummary(BaseModel):
    tick: int
    resources: Dict[str, float]
    territories: int
    events: int


class AgentSummary(BaseModel):
    agent_id: str
    name: str
    agent_class: str
    wealth: float
    health: float
    energy: float
    age: int
    alive: bool
    territory_id: Optional[int]


class EconomySummary(BaseModel):
    gdp: float
    inflation: float
    employment: float
    inequality: float
    companies: int
    prices: Dict[str, float]


class GovernanceSummary(BaseModel):
    government_type: str
    officials: int
    laws: int
    stability: float
    legitimacy: float
    tax_rate: float


class MetricsSummary(BaseModel):
    current: Dict[str, Any]
    trends: Dict[str, float]


class FullSummary(BaseModel):
    world: WorldSummary
    economy: EconomySummary
    governance: GovernanceSummary
    metrics: MetricsSummary
    agents: Dict[str, Any]
    culture: Dict[str, Any]
    events: Dict[str, Any]
