from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class Relationship:
    target_id: str
    trust: float
    influence: float
    familiarity: int = 0
    relationship_type: str = "neutral"

    def interact(self):
        self.familiarity += 1
        delta = random.gauss(0.01, 0.02)
        self.trust = max(0.0, min(1.0, self.trust + delta))

    def as_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "trust": round(self.trust, 3),
            "influence": round(self.influence, 3),
            "familiarity": self.familiarity,
            "type": self.relationship_type,
        }


@dataclass
class SocialGroup:
    id: str
    name: str
    group_type: str
    members: Set[str] = field(default_factory=set)
    shared_beliefs: List[str] = field(default_factory=list)
    cohesion: float = 0.5

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.group_type,
            "members": len(self.members),
            "cohesion": round(self.cohesion, 3),
        }


class SocialNetwork:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.relationships: Dict[str, Relationship] = {}
        self.groups: List[str] = []

    def add_relationship(self, target_id: str,
                         trust: float = 0.5,
                         influence: float = 0.3,
                         relationship_type: str = "neutral"):
        if target_id not in self.relationships:
            self.relationships[target_id] = Relationship(
                target_id=target_id,
                trust=trust,
                influence=influence,
                relationship_type=relationship_type,
            )

    def get_trusted(self, min_trust: float = 0.6) -> List[Relationship]:
        return [r for r in self.relationships.values() if r.trust >= min_trust]

    def get_influential(self, min_influence: float = 0.5) -> List[Relationship]:
        return [r for r in self.relationships.values() if r.influence >= min_influence]

    def spread_belief(self, belief: str, agents: Dict[str, "Agent"]):
        for rel in self.get_trusted(0.5):
            if rel.target_id in agents:
                target = agents[rel.target_id]
                target.knowledge.add_shared_knowledge(
                    proposition=belief,
                    confidence=rel.trust * 0.8,
                    source=self.agent_id,
                )

    def join_group(self, group_id: str, groups: Dict[str, SocialGroup]):
        if group_id not in self.groups:
            self.groups.append(group_id)
            if group_id in groups:
                groups[group_id].members.add(self.agent_id)

    def summarize(self) -> dict:
        return {
            "relationships": len(self.relationships),
            "groups": len(self.groups),
            "avg_trust": round(
                sum(r.trust for r in self.relationships.values()) /
                max(1, len(self.relationships)), 3
            ),
        }
