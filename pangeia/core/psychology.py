from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Personality:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    @classmethod
    def random(cls, rng: random.Random) -> "Personality":
        return cls(
            openness=rng.gauss(0.5, 0.15),
            conscientiousness=rng.gauss(0.5, 0.15),
            extraversion=rng.gauss(0.5, 0.15),
            agreeableness=rng.gauss(0.5, 0.15),
            neuroticism=rng.gauss(0.5, 0.15),
        )

    def as_dict(self) -> dict:
        return {
            "openness": round(self.openness, 3),
            "conscientiousness": round(self.conscientiousness, 3),
            "extraversion": round(self.extraversion, 3),
            "agreeableness": round(self.agreeableness, 3),
            "neuroticism": round(self.neuroticism, 3),
        }

    def mutate(self, rate: float = 0.05, rng: Optional[random.Random] = None):
        if rng is None:
            rng = random
        for attr in ["openness", "conscientiousness", "extraversion",
                      "agreeableness", "neuroticism"]:
            if rng.random() < rate:
                delta = rng.gauss(0, 0.05)
                setattr(self, attr, max(0.0, min(1.0, getattr(self, attr) + delta)))


@dataclass
class EmotionalState:
    happiness: float = 0.5
    trust: float = 0.5
    anger: float = 0.0
    fear: float = 0.0
    curiosity: float = 0.5

    def update(self, delta_happiness: float = 0, delta_trust: float = 0,
               delta_anger: float = 0, delta_fear: float = 0,
               delta_curiosity: float = 0):
        self.happiness = max(0.0, min(1.0, self.happiness + delta_happiness))
        self.trust = max(0.0, min(1.0, self.trust + delta_trust))
        self.anger = max(0.0, min(1.0, self.anger + delta_anger))
        self.fear = max(0.0, min(1.0, self.fear + delta_fear))
        self.curiosity = max(0.0, min(1.0, self.curiosity + delta_curiosity))

    def as_dict(self) -> dict:
        return {
            "happiness": round(self.happiness, 3),
            "trust": round(self.trust, 3),
            "anger": round(self.anger, 3),
            "fear": round(self.fear, 3),
            "curiosity": round(self.curiosity, 3),
        }


@dataclass
class Goal:
    description: str
    priority: float
    goal_type: str
    target: str = ""
    deadline: Optional[float] = None
    progress: float = 0.0

    def as_dict(self) -> dict:
        return {
            "description": self.description,
            "priority": round(self.priority, 3),
            "type": self.goal_type,
            "target": self.target,
            "progress": round(self.progress, 3),
        }
