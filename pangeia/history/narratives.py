from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class HistoricalNarrative:
    id: str
    event_tick: int
    event_type: str
    title: str
    description: str
    perspective: str
    supporters: List[str] = field(default_factory=list)
    accuracy: float = 0.5

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "event_tick": self.event_tick,
            "event_type": self.event_type,
            "title": self.title,
            "perspective": self.perspective,
            "supporters": len(self.supporters),
            "accuracy": round(self.accuracy, 2),
        }


class NarrativeSystem:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.narratives: Dict[str, HistoricalNarrative] = {}
        self.timeline: List[dict] = []

    def record_event(self, event: dict):
        self.timeline.append({
            "tick": event.get("tick", 0),
            "type": event.get("type", "unknown"),
            "description": event.get("description", ""),
        })
        if len(self.timeline) > 1000:
            self.timeline = self.timeline[-500:]

    def generate_narratives(self, event: dict, agents: Dict[str, Agent], tick: int):
        if self.rng.random() < 0.3:
            return

        event_type = event.get("type", "unknown")
        description = event.get("description", "an event")

        perspectives = [
            ("Official History", 0.7,
             f"The official record states that {description.lower()}"),
            ("Popular Memory", 0.5,
             f"Among the people, it is said that {description.lower()}"),
            ("Critical Analysis", 0.3,
             f"Revisionist scholars argue that {description.lower()} was misinterpreted"),
        ]

        for title, accuracy, base_desc in perspectives:
            if self.rng.random() < 0.5:
                continue
            narrative_id = f"narr_{len(self.narratives)}"
            narrative = HistoricalNarrative(
                id=narrative_id,
                event_tick=tick,
                event_type=event_type,
                title=title,
                description=base_desc,
                perspective=title,
                accuracy=accuracy * self.rng.uniform(0.7, 1.3),
            )
            narrative.supporters.append(
                self.rng.choice([a.agent_id for a in agents.values() if a.state.is_alive])
            )
            self.narratives[narrative_id] = narrative

            for agent in agents.values():
                if (agent.state.is_alive
                        and self.rng.random() < 0.05
                        and agent.state.education_level > 0.5):
                    agent.knowledge.add_shared_knowledge(
                        proposition=narrative.description[:60],
                        confidence=self.rng.uniform(0.2, 0.6),
                        source="history",
                        category="history",
                    )
                    agent.memory.remember(
                        f"Learned: {narrative.title} - {narrative.description[:40]}",
                        memory_type="history", importance=0.5,
                    )

    def summary(self) -> dict:
        return {
            "narratives": len(self.narratives),
            "timeline_events": len(self.timeline),
            "recent_narratives": [
                n.as_dict() for n in list(self.narratives.values())[-10:]
            ],
            "timeline_preview": self.timeline[-20:] if self.timeline else [],
        }
