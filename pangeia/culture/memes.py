from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


@dataclass
class Meme:
    id: str
    content: str
    origin_id: str
    fitness: float
    variants: int = 0
    spread_count: int = 0

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content[:50],
            "origin": self.origin_id,
            "fitness": round(self.fitness, 3),
            "variants": self.variants,
            "spread": self.spread_count,
        }


class MemePool:
    def __init__(self):
        self.memes: Dict[str, Meme] = {}

    def create_meme(self, content: str, origin_id: str,
                    fitness: float = 0.5) -> Meme:
        meme_id = f"meme_{len(self.memes)}"
        meme = Meme(
            id=meme_id,
            content=content,
            origin_id=origin_id,
            fitness=fitness,
        )
        self.memes[meme_id] = meme
        return meme

    def spread(self, agents: Dict[str, "Agent"]):
        alive_ids = [aid for aid, a in agents.items() if a.state.is_alive]
        alive_map = {aid: agents[aid] for aid in alive_ids}

        for meme in list(self.memes.values()):
            spreaders = [
                aid for aid in alive_ids
                if alive_map[aid].knowledge.get_belief(meme.content[:50])
            ]
            sample_size = min(5, len(alive_ids))
            for aid in spreaders:
                if sample_size > 0 and random.random() < 0.05 * meme.fitness:
                    target = random.choice(alive_ids)
                    if target != aid and target in alive_map:
                        alive_map[target].knowledge.add_shared_knowledge(
                            proposition=meme.content[:50],
                            confidence=0.4,
                            source=aid,
                            category="meme",
                        )
                        meme.spread_count += 1

            if random.random() < 0.01 * meme.fitness:
                variant = meme.content + " [evolved]"
                self.create_meme(variant, meme.origin_id,
                                 fitness=meme.fitness * random.uniform(0.8, 1.2))
                meme.variants += 1

    def summarize(self) -> dict:
        return {
            "total_memes": len(self.memes),
            "avg_fitness": round(
                sum(m.fitness for m in self.memes.values()) / max(1, len(self.memes)), 3
            ),
            "most_spread": max(self.memes.values(), key=lambda m: m.spread_count).as_dict()
            if self.memes else None,
        }
