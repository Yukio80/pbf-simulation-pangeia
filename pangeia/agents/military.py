from __future__ import annotations

from typing import List, TYPE_CHECKING

from pangeia.core.agent import Agent

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class Military(Agent):
    def __init__(self, config, rng=None):
        super().__init__("military", config, rng)
        self.strength: float = 1.0
        self.loyalty: float = 0.8
        self.missions: List[str] = []
        self.add_goal("Protect territory", 0.9, "defense")
        self.add_goal("Maintain order", 0.7, "security")

    def decide(self, sim: "Simulation") -> List[str]:
        actions = []
        if not self.state.is_alive:
            return ["dead"]

        perception = self.perceive(sim)
        world = sim.world

        actions.append("patrolling")

        resource_crisis = any(
            perception["resources"].get(r, 0) < 1000
            for r in ["energy", "water", "food"]
        )
        if resource_crisis:
            if self.loyalty > 0.5:
                actions.append("protecting_resources")
                self.memory.remember(
                    "Securing critical resources",
                    memory_type="operation",
                    importance=0.7,
                )
            else:
                actions.append("opportunistic")

        if self.rng.random() < 0.01:
            self.strength *= 1.05

        self.loyalty += self.rng.gauss(0, 0.01)
        self.loyalty = max(0, min(1, self.loyalty))

        self.consume_resources()
        return actions
