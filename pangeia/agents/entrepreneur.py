from __future__ import annotations

from typing import List, TYPE_CHECKING

from pangeia.core.agent import Agent

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class Entrepreneur(Agent):
    def __init__(self, config, rng=None):
        super().__init__("entrepreneur", config, rng)
        self.venture_count = 0
        self.add_goal("Maximize profit", 0.9, "economic")
        self.add_goal("Build companies", 0.8, "economic")

    def decide(self, sim: "Simulation") -> List[str]:
        actions = []
        if not self.state.is_alive:
            return ["dead"]

        perception = self.perceive(sim)

        if self.state.wealth > 500 and self.rng.random() < 0.3:
            actions.append("starting_company")
            self.venture_count += 1
            self.memory.remember(
                f"Started a new venture (venture #{self.venture_count})",
                memory_type="business",
                importance=0.8,
            )
            cost = sim.config.economy.company_startup_cost
            self.state.wealth -= cost * self.rng.uniform(0.5, 1.5)

        if self.state.energy < 20:
            actions.append("resting")
        else:
            actions.append("managing")

        if sim.economy:
            indicators = sim.economy.indicators
            if indicators.inflation > 0.1:
                self.emotions.update(delta_fear=0.03)

        self.consume_resources()
        return actions
