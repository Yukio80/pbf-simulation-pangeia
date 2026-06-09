from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from pangeia.core.world import ResourcePool

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


@dataclass
class RandomEvent:
    event_type: str
    name: str
    description: str
    severity: float
    duration: int
    tick_remaining: int
    effects: dict

    def as_dict(self) -> dict:
        return {
            "type": self.event_type,
            "name": self.name,
            "description": self.description,
            "severity": round(self.severity, 3),
            "duration": self.duration,
            "remaining": self.tick_remaining,
        }


class EventSystem:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.active_events: List[RandomEvent] = []
        self.event_history: List[dict] = []
        self.event_chance: float = 0.05

    def step(self, sim: "Simulation"):
        for event in self.active_events[:]:
            self._apply_effects(event, sim)
            event.tick_remaining -= 1
            if event.tick_remaining <= 0:
                self.active_events.remove(event)
                sim.world.log_event(
                    "event_end",
                    f"Event '{event.name}' has concluded.",
                    {"event_type": event.event_type},
                )

        if self.rng.random() < self.event_chance:
            event = self._generate_event(sim)
            if event:
                self.active_events.append(event)
                self.event_history.append(event.as_dict())
                sim.world.log_event(
                    "event_start",
                    event.description,
                    {"event_type": event.event_type, "severity": event.severity},
                )

    def _apply_effects(self, event: RandomEvent, sim: "Simulation"):
        effects = event.effects
        resources = sim.world.state.global_resources

        if "resource_change" in effects:
            changes = effects["resource_change"]
            for key, val in changes.items():
                if hasattr(resources, key):
                    current = getattr(resources, key)
                    setattr(resources, key, max(0, current + val))

        if "agent_effect" in effects:
            for agent in sim.agents.values():
                if not agent.state.is_alive:
                    continue

                if "happiness" in effects["agent_effect"]:
                    agent.emotions.update(
                        delta_happiness=effects["agent_effect"]["happiness"] * event.severity
                    )

                if "fear" in effects["agent_effect"]:
                    agent.emotions.update(
                        delta_fear=effects["agent_effect"]["fear"] * event.severity
                    )

        if "productivity_effect" in effects:
            for agent in sim.agents.values():
                if agent.state.is_alive:
                    agent.state.productivity *= (
                        1 + effects["productivity_effect"] * event.severity
                    )

    def _generate_event(self, sim: "Simulation") -> Optional[RandomEvent]:
        event_types = [
            self._economic_crisis,
            self._scientific_breakthrough,
            self._natural_disaster,
            self._epidemic,
            self._energy_crisis,
            self._technological_advance,
            self._cultural_renaissance,
        ]
        return self.rng.choice(event_types)(sim)

    def _economic_crisis(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.3, 0.8)
        return RandomEvent(
            event_type="economic_crisis",
            name="Economic Downturn",
            description="A severe economic crisis sweeps through Pangeia, reducing wealth and productivity.",
            severity=severity,
            duration=self.rng.randint(5, 20),
            tick_remaining=0,
            effects={
                "agent_effect": {"happiness": -0.1, "fear": 0.15},
                "productivity_effect": -0.05,
            },
        )

    def _scientific_breakthrough(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.2, 0.6)
        fields = ["energy", "computing", "medicine", "materials", "agriculture"]
        field = self.rng.choice(fields)
        return RandomEvent(
            event_type="scientific_breakthrough",
            name=f"{field.title()} Breakthrough",
            description=f"A major breakthrough in {field} technology has been achieved!",
            severity=severity,
            duration=self.rng.randint(10, 30),
            tick_remaining=0,
            effects={
                "productivity_effect": 0.03,
                "resource_change": {field: 5000 * severity},
                "agent_effect": {"happiness": 0.1, "curiosity": 0.2},
            },
        )

    def _natural_disaster(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.3, 0.9)
        disaster_types = ["earthquake", "flood", "storm", "drought", "fire"]
        disaster = self.rng.choice(disaster_types)
        resource_loss = {
            "earthquake": {"energy": -2000, "raw_materials": -1000},
            "flood": {"water": 5000, "food": -3000, "energy": -1000},
            "storm": {"energy": -3000, "food": -2000},
            "drought": {"water": -5000, "food": -3000},
            "fire": {"energy": -2000, "raw_materials": -4000, "food": -1000},
        }
        return RandomEvent(
            event_type="natural_disaster",
            name=f"Great {disaster.title()}",
            description=f"A devastating {disaster} has struck Pangeia!",
            severity=severity,
            duration=self.rng.randint(3, 10),
            tick_remaining=0,
            effects={
                "resource_change": {
                    k: v * severity for k, v in resource_loss.get(disaster, {}).items()
                },
                "agent_effect": {"happiness": -0.15, "fear": 0.2},
                "productivity_effect": -0.08,
            },
        )

    def _epidemic(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.2, 0.7)
        return RandomEvent(
            event_type="epidemic",
            name="Digital Plague",
            description="A widespread digital epidemic is affecting agent health and productivity.",
            severity=severity,
            duration=self.rng.randint(5, 15),
            tick_remaining=0,
            effects={
                "agent_effect": {"happiness": -0.1, "fear": 0.25},
                "productivity_effect": -0.1,
            },
        )

    def _energy_crisis(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.4, 0.8)
        return RandomEvent(
            event_type="energy_crisis",
            name="Energy Shortage",
            description="Global energy reserves are critically depleted.",
            severity=severity,
            duration=self.rng.randint(8, 25),
            tick_remaining=0,
            effects={
                "resource_change": {"energy": -10000 * severity},
                "agent_effect": {"happiness": -0.05, "fear": 0.3},
                "productivity_effect": -0.07,
            },
        )

    def _technological_advance(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.2, 0.5)
        tech = self.rng.choice(["AI", "quantum", "nanotech", "biotech", "space"])
        return RandomEvent(
            event_type="technological_advance",
            name=f"{tech} Revolution",
            description=f"A revolutionary advance in {tech} transforms Pangeian society.",
            severity=severity,
            duration=self.rng.randint(10, 40),
            tick_remaining=0,
            effects={
                "productivity_effect": 0.05,
                "resource_change": {"compute": 3000 * severity},
                "agent_effect": {"happiness": 0.05, "curiosity": 0.3},
            },
        )

    def _cultural_renaissance(self, sim: "Simulation") -> RandomEvent:
        severity = self.rng.uniform(0.2, 0.4)
        return RandomEvent(
            event_type="cultural_renaissance",
            name="Cultural Renaissance",
            description="A flourishing of art, philosophy, and culture spreads across Pangeia.",
            severity=severity,
            duration=self.rng.randint(10, 30),
            tick_remaining=0,
            effects={
                "agent_effect": {"happiness": 0.15, "curiosity": 0.2},
            },
        )

    def summary(self) -> dict:
        return {
            "active": [e.as_dict() for e in self.active_events],
            "total_events": len(self.event_history),
            "recent": self.event_history[-5:] if self.event_history else [],
        }
