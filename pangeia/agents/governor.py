from __future__ import annotations

from typing import List, TYPE_CHECKING

from pangeia.core.agent import Agent

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class Governor(Agent):
    def __init__(self, config, rng=None):
        super().__init__("governor", config, rng)
        self.state.political_alignment = self.rng.uniform(-0.5, 0.5)
        self.policies_enacted: List[str] = []
        self.popularity: float = 0.5
        self.add_goal("Maintain power", 0.9, "political")
        self.add_goal("Govern effectively", 0.8, "governance")

    def decide(self, sim: "Simulation") -> List[str]:
        actions = []
        if not self.state.is_alive:
            return ["dead"]

        perception = self.perceive(sim)

        if sim.economy:
            if perception["economy"].get("gdp", 0) < 1000:
                actions.append("economic_policy")
                self.memory.remember(
                    "Enacted economic stimulus policy",
                    memory_type="governance",
                    importance=0.7,
                )
                self.policies_enacted.append("economic_stimulus")

        if perception["resources"].get("energy", 0) < 50000:
            actions.append("resource_policy")
            self.memory.remember(
                "Enacted resource conservation policy",
                memory_type="governance",
                importance=0.7,
            )
            self.policies_enacted.append("resource_conservation")

        if self.rng.random() < 0.2:
            actions.append("make_speech")

        self.popularity += self.rng.gauss(0, 0.02)

        if sim.governance:
            government = sim.governance
            if self in government.officials:
                self.state.influence = 0.5 + self.popularity * 0.3

        self.consume_resources()
        return actions
