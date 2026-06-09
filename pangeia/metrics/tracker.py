from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


@dataclass
class MetricsSnapshot:
    tick: int
    cooperation: float
    conflict: float
    polarization: float
    innovation: float
    stability: float
    power_concentration: float
    social_mobility: float
    collective_happiness: float
    institutional_resilience: float
    population: int
    alive: int

    def as_dict(self) -> dict:
        return {
            "tick": self.tick,
            "cooperation": round(self.cooperation, 4),
            "conflict": round(self.conflict, 4),
            "polarization": round(self.polarization, 4),
            "innovation": round(self.innovation, 4),
            "stability": round(self.stability, 4),
            "power_concentration": round(self.power_concentration, 4),
            "social_mobility": round(self.social_mobility, 4),
            "collective_happiness": round(self.collective_happiness, 4),
            "institutional_resilience": round(self.institutional_resilience, 4),
            "population": self.population,
            "alive": self.alive,
        }


class MetricsTracker:
    def __init__(self):
        self.history: List[MetricsSnapshot] = []

    def record(self, sim: "Simulation"):
        agents = sim.agents
        alive = [a for a in agents.values() if a.state.is_alive]
        total = len(agents)

        happinesses = [a.emotions.happiness for a in alive] if alive else [0]
        avg_happiness = sum(happinesses) / len(happinesses)

        coop = sum(1 for a in agents.values()
                   if a.social.relationships and a.state.is_alive) / max(1, total)

        alignments = [a.state.political_alignment for a in alive if a.state.is_alive]
        pol = 0.0
        if len(alignments) > 1:
            pol = sum(abs(a - sum(alignments) / len(alignments)) for a in alignments) \
                / max(1, len(alignments))

        if sim.economy:
            ineq = sim.economy.indicators.inequality
        else:
            ineq = 0.5

        if sim.governance:
            gov = sim.governance
            stab = gov.government.stability
            legit = gov.government.legitimacy
        else:
            stab = 0.5
            legit = 0.5

        power = ineq * 0.7 + pol * 0.3

        snapshot = MetricsSnapshot(
            tick=sim.world.state.tick,
            cooperation=coop,
            conflict=1.0 - coop,
            polarization=pol,
            innovation=sim.economy.indicators.tech_level if sim.economy else 0.3,
            stability=stab,
            power_concentration=power,
            social_mobility=1.0 - ineq,
            collective_happiness=avg_happiness,
            institutional_resilience=(stab + legit) / 2,
            population=total,
            alive=len(alive),
        )
        self.history.append(snapshot)
        return snapshot

    def summary(self, n: int = 10) -> dict:
        recent = self.history[-n:] if self.history else []
        if not recent:
            return {}
        return {
            "current": recent[-1].as_dict() if recent else {},
            "trends": {
                "avg_cooperation": round(sum(m.cooperation for m in recent) / len(recent), 4),
                "avg_conflict": round(sum(m.conflict for m in recent) / len(recent), 4),
                "avg_polarization": round(sum(m.polarization for m in recent) / len(recent), 4),
                "avg_happiness": round(sum(m.collective_happiness for m in recent) / len(recent), 4),
                "avg_stability": round(sum(m.stability for m in recent) / len(recent), 4),
            },
            "history_length": len(self.history),
        }
