from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class Ideology:
    id: str
    name: str
    principles: List[str]
    values: Dict[str, float]
    origin_id: str
    followers: Set[str] = field(default_factory=set)
    influence: float = 0.1
    birth_tick: int = 0
    hostility: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "principles": self.principles,
            "values": self.values,
            "followers": len(self.followers),
            "influence": round(self.influence, 4),
            "birth_tick": self.birth_tick,
        }


class IdeologySystem:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.ideologies: Dict[str, Ideology] = {}

    def step(self, agents: Dict[str, Agent], tick: int):
        alive_ids = [aid for aid, a in agents.items() if a.state.is_alive]
        alive_map = {aid: agents[aid] for aid in alive_ids}

        for agent in alive_map.values():
            if (self.rng.random() < 0.01 * agent.state.influence
                    and len(self.ideologies) < 20):
                ideology = self._synthesize_ideology(agent, tick)
                if ideology:
                    self.ideologies[ideology.id] = ideology
                    agent.memory.remember(
                        f"Founded ideology: {ideology.name}",
                        memory_type="ideology", importance=1.0,
                    )
                    agent.state.influence += 0.1

        for ideology in list(self.ideologies.values()):
            ideology.influence *= (1 + self.rng.gauss(0.001, 0.005))
            ideology.influence = min(1.0, max(0.0, ideology.influence))

            for fid in list(ideology.followers):
                if fid not in alive_map:
                    ideology.followers.discard(fid)
                    continue
                follower = alive_map[fid]
                sample_size = min(5, len(alive_ids))
                prospects = self.rng.sample(alive_ids, sample_size) if sample_size else []
                for other_id in prospects:
                    if other_id == fid or other_id in ideology.followers:
                        continue
                    other = alive_map[other_id]
                    if self.rng.random() < 0.01 * ideology.influence:
                        proximity = follower.social.relationships.get(other_id)
                        if proximity and proximity.trust > 0.4:
                            self._convert_to_ideology(other, ideology)

    def _synthesize_ideology(self, founder: Agent, tick: int) -> Optional[Ideology]:
        existing_names = {i.name for i in self.ideologies.values()}

        templates = [
            ("{adj}{core}", [
                "Techno", "Bio", "Crypto", "Neuro", "Data", "Solar",
                "Quantum", "Cyber", "Eco", "Info",
            ], [
                "communism", "socialism", "capitalism", "libertarianism",
                "collectivism", "individualism", "meritocracy", "egalitarianism",
                "transhumanism", "primitivism", "accelerationism", "mutualism",
            ]),
            ("{core}{adj}", [
                "Techno", "Bio", "Crypto", "Neuro", "Data", "Solar",
            ], [
                "communism", "socialism", "capitalism", "libertarianism",
            ]),
            ("{core}", [
                "The Great Harmony", "The Collective Path", "The Sovereign Individual",
                "The Digital Commonwealth", "The Organic Order", "The Rational Society",
                "The Merit Republic", "The Anarchist Federation", "The Technate",
                "The Solar Collective", "The Cybernetic Union", "The Eco Commune",
            ], []),
        ]

        pattern, cores, suffixes = self.rng.choice(templates)
        for _ in range(20):
            if pattern == "{adj}{core}":
                name = f"{self.rng.choice(cores)}{self.rng.choice(suffixes)}"
            elif pattern == "{core}{adj}":
                name = f"{self.rng.choice(suffixes).title()}{self.rng.choice(cores)}"
            else:
                name = self.rng.choice(cores)
            if name not in existing_names:
                break
        else:
            name = f"Ideology_{len(self.ideologies)}"

        economic = self.rng.uniform(-1, 1)
        social = self.rng.uniform(-1, 1)
        governance = self.rng.uniform(-1, 1)
        progress = self.rng.uniform(-1, 1)

        principles = [
            self._principle_for(economic, "economic"),
            self._principle_for(social, "social"),
            self._principle_for(governance, "governance"),
        ]

        ideology = Ideology(
            id=f"ideo_{len(self.ideologies)}",
            name=name,
            principles=principles,
            values={
                "economic_freedom": economic,
                "social_freedom": social,
                "governance_decentralization": governance,
                "progress_orientation": progress,
            },
            origin_id=founder.agent_id,
            birth_tick=tick,
        )
        ideology.followers.add(founder.agent_id)
        return ideology

    def _principle_for(self, value: float, domain: str) -> str:
        if domain == "economic":
            if value > 0.3:
                return "Free markets and private property are the foundation of prosperity"
            elif value < -0.3:
                return "Collective ownership of means of production ensures justice"
            return "A mixed economy balances individual initiative and common good"
        elif domain == "social":
            if value > 0.3:
                return "Individual liberty is the highest social value"
            elif value < -0.3:
                return "The collective good supersedes individual desires"
            return "Social harmony requires balancing rights and responsibilities"
        else:
            if value > 0.3:
                return "Power should be distributed to the smallest effective unit"
            elif value < -0.3:
                return "Strong central governance ensures stability and progress"
            return "Governance should be efficient, accountable, and adaptive"

    def _convert_to_ideology(self, agent: Agent, ideology: Ideology):
        ideology.followers.add(agent.agent_id)
        for principle in ideology.principles:
            agent.knowledge.add_shared_knowledge(
                proposition=principle,
                confidence=self.rng.uniform(0.3, 0.7),
                source=ideology.origin_id,
                category="ideology",
            )
        agent.memory.remember(
            f"Adopted ideology: {ideology.name}",
            memory_type="ideology", importance=0.6,
        )

    def summary(self) -> dict:
        sorted_ideos = sorted(
            self.ideologies.values(),
            key=lambda i: len(i.followers),
            reverse=True,
        )
        return {
            "total_ideologies": len(self.ideologies),
            "ideologies": [i.as_dict() for i in sorted_ideos[:10]],
            "total_followers": sum(
                len(i.followers) for i in self.ideologies.values()
            ),
        }
