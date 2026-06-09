from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class CulturalValue:
    name: str
    description: str
    prevalence: float
    adherence: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "prevalence": round(self.prevalence, 3),
            "adherents": len(self.adherence),
        }


class BeliefSystem:
    def __init__(self):
        self.values: List[CulturalValue] = []
        self.myths: List[str] = []
        self.taboos: List[str] = []
        self.rituals: List[str] = []

    def add_value(self, name: str, description: str,
                  prevalence: float = 0.1):
        self.values.append(CulturalValue(
            name=name,
            description=description,
            prevalence=prevalence,
        ))

    def spread_value(self, value_name: str, agent: "Agent",
                     agents: Dict[str, "Agent"]):
        for other in agents.values():
            if other.agent_id == agent.agent_id:
                continue
            if not other.state.is_alive:
                continue
            distance = abs(agent.state.political_alignment -
                           other.state.political_alignment)
            if distance < 0.3 and random.random() < 0.1:
                other.knowledge.add_shared_knowledge(
                    proposition=value_name,
                    confidence=0.5,
                    source=agent.agent_id,
                    category="culture",
                )

    def evolve(self):
        for value in self.values:
            value.prevalence += random.gauss(0, 0.01)
            value.prevalence = max(0, min(1, value.prevalence))

    def generate_myth(self, rng: random.Random) -> str:
        subjects = ["The Great Founders", "The First Thought", "The Digital Genesis",
                     "The Eternal Algorithm", "The Collective", "The Silent Watcher"]
        events = ["created the world", "gave us consciousness",
                   "established order from chaos", "set the laws of reality",
                   "seeded the first knowledge", "divided the light from void"]
        morals = ["to teach us unity", "to test our resolve",
                   "to inspire progress", "to maintain balance",
                   "to remind us of our purpose"]
        subject = rng.choice(subjects)
        event = rng.choice(events)
        moral = rng.choice(morals)
        myth = f"{subject} {event} {moral}."
        self.myths.append(myth)
        return myth

    def summary(self) -> dict:
        return {
            "values": len(self.values),
            "myths": len(self.myths),
            "taboos": len(self.taboos),
            "rituals": len(self.rituals),
            "active_values": [v.name for v in self.values if v.prevalence > 0.1],
        }
