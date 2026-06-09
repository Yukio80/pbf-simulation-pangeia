from __future__ import annotations

from typing import List, TYPE_CHECKING

from pangeia.core.agent import Agent

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class Citizen(Agent):
    def __init__(self, config, rng=None):
        super().__init__("citizen", config, rng)
        self.add_goal("Survive and prosper", 0.9, "survival")
        self.add_goal("Build wealth", 0.7, "economic")

    def decide(self, sim: "Simulation") -> List[str]:
        actions = []
        if not self.state.is_alive:
            return ["dead"]

        perception = self.perceive(sim)

        if self.state.energy < 20:
            actions.append("resting")
        elif self.state.employer_id:
            actions.append("working")
        elif self.state.wealth < 50:
            actions.append("seeking_job")
        else:
            actions.append("consuming")

        if self.rng.random() < 0.6:
            actions.append("socializing")
        if self.rng.random() < 0.1:
            actions.append("learning")

        self.consume_resources()

        for resource_name in ["energy", "water", "food"]:
            val = perception["resources"].get(resource_name, 0)
            if val < 1000:
                self.emotions.update(delta_fear=0.05)

        if self.state.wealth > 200:
            self.emotions.update(delta_happiness=0.02)
        elif self.state.wealth < 20:
            self.emotions.update(delta_happiness=-0.03)

        return actions
