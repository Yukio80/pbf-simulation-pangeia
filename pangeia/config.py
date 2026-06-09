from dataclasses import dataclass, field
from typing import Optional

from pangeia.persistence.config import PersistenceConfig


@dataclass
class WorldConfig:
    name: str = "Pangeia"
    seed: int = 42
    tick_interval: float = 0.1
    max_ticks: Optional[int] = None

    initial_population: int = 500
    max_population: int = 10_000

    territory_size: int = 1_000_000


@dataclass
class ResourceConfig:
    energy: float = 1_000_000
    water: float = 1_000_000
    food: float = 1_000_000
    raw_materials: float = 500_000
    compute: float = 100_000

    energy_regen: float = 5000
    water_regen: float = 5000
    food_regen: float = 3000
    raw_materials_regen: float = 1000
    compute_regen: float = 500


@dataclass
class AgentConfig:
    base_energy_consumption: float = 1.0
    base_food_consumption: float = 0.5
    base_water_consumption: float = 0.3
    base_compute_cost: float = 0.1

    min_wealth: float = 0.0
    starting_wealth: float = 100.0
    max_health: float = 100.0

    knowledge_decay_rate: float = 0.001
    max_knowledge_items: int = 100
    memory_capacity: int = 200
    communication_range: float = 50.0


@dataclass
class EconomyConfig:
    base_salary: float = 10.0
    tax_rate: float = 0.1
    interest_rate: float = 0.02
    inflation_target: float = 0.02
    company_startup_cost: float = 500.0
    max_companies: int = 1000
    trade_friction: float = 0.05


@dataclass
class GovernanceConfig:
    min_tax_rate: float = 0.0
    max_tax_rate: float = 0.5
    base_tax_rate: float = 0.1
    election_cycle: int = 50
    min_voter_turnout: float = 0.3


@dataclass
class SimulationConfig:
    world: WorldConfig = field(default_factory=WorldConfig)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    economy: EconomyConfig = field(default_factory=EconomyConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)

    @classmethod
    def default(cls) -> "SimulationConfig":
        return cls()
