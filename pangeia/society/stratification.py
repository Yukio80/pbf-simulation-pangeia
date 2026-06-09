from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class SocialClass:
    name: str
    description: str
    min_wealth: float
    max_wealth: float
    members: List[str] = field(default_factory=list)
    influence_multiplier: float = 1.0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "members": len(self.members),
            "influence_multiplier": self.influence_multiplier,
        }


CLASS_DEFINITIONS = [
    SocialClass("elite", "Concentrates wealth and power", 500, float("inf"), influence_multiplier=3.0),
    SocialClass("upper_middle", "Professionals and successful entrepreneurs", 200, 500, influence_multiplier=1.5),
    SocialClass("middle", "Workers with stable income", 80, 200, influence_multiplier=1.0),
    SocialClass("lower", "Low-income workers", 20, 80, influence_multiplier=0.5),
    SocialClass("excluded", "Below poverty line", float("-inf"), 20, influence_multiplier=0.1),
]


class StratificationSystem:
    def __init__(self):
        self.classes = CLASS_DEFINITIONS
        self.mobility_history: List[float] = []

    def assign_classes(self, agents: Dict[str, Agent]):
        for cls in self.classes:
            cls.members = []

        for agent in agents.values():
            if not agent.state.is_alive:
                continue
            wealth = agent.state.wealth
            for cls in self.classes:
                if cls.min_wealth <= wealth < cls.max_wealth:
                    cls.members.append(agent.agent_id)
                    agent.state.influence = max(
                        agent.state.influence,
                        cls.influence_multiplier * 0.1,
                    )
                    break

    def track_mobility(self):
        total = sum(len(c.members) for c in self.classes)
        if total == 0:
            return
        gini = 0.0
        proportions = [len(c.members) / total for c in self.classes]
        for p in proportions:
            gini += p ** 2
        gini = 1 - gini
        self.mobility_history.append(gini)
        if len(self.mobility_history) > 1000:
            self.mobility_history = self.mobility_history[-500:]

    def summary(self) -> dict:
        return {
            "classes": [c.as_dict() for c in self.classes],
            "mobility_index": self.mobility_history[-1] if self.mobility_history else 0.5,
            "mobility_trend": (
                self.mobility_history[-1] - self.mobility_history[0]
            ) / max(1, len(self.mobility_history))
            if len(self.mobility_history) > 1 else 0,
        }
