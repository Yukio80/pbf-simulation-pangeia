from __future__ import annotations

from typing import List, TYPE_CHECKING

from pangeia.core.agent import Agent

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class Researcher(Agent):
    def __init__(self, config, rng=None):
        super().__init__("researcher", config, rng)
        self.discoveries: List[str] = []
        self.state.education_level = 0.7
        self.state.productivity = 1.5
        self.add_goal("Advance knowledge", 0.9, "knowledge")
        self.add_goal("Make discoveries", 0.8, "innovation")

    def decide(self, sim: "Simulation") -> List[str]:
        actions = []
        if not self.state.is_alive:
            return ["dead"]

        if self.state.energy < 20:
            actions.append("resting")
        else:
            actions.append("researching")
            self.work(base_output=1.5)
            if sim.technology:
                researchable = sim.technology.get_researchable()
                if researchable and self.rng.random() < 0.4:
                    target = self.rng.choice(researchable)
                    progress = self.state.education_level * 2.0 * self.rng.uniform(0.5, 1.5)
                    discovered = sim.technology.research(target.id, progress, self.agent_id)
                    if discovered:
                        self.discoveries.append(target.name)
                        self.memory.remember(
                            f"Discovered technology: {target.name}",
                            memory_type="discovery", importance=1.0,
                        )
                        self.state.influence += 0.15
                        actions.append(f"discovered:{target.name}")
                    else:
                        actions.append(f"researching:{target.name}")
                else:
                    progress = self.work(base_output=1.0)
                    self.state.wealth += progress * 0.3

        self.learn(f"research_{self.rng.randint(1, 10)}", 0.02)
        self.consume_resources()
        return actions
