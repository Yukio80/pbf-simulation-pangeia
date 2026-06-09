from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class ElectionResult:
    winner_id: str
    votes_cast: int
    total_voters: int
    turnout: float
    margin: float
    tick: int


class ElectionSystem:
    def __init__(self):
        self.results: List[ElectionResult] = []

    def run_election(self, agents: Dict[str, "Agent"],
                     candidates: List[str],
                     tick: int) -> ElectionResult:
        votes: Dict[str, int] = {}
        total_voters = 0

        for agent in agents.values():
            if not agent.state.is_alive:
                continue
            total_voters += 1
            if agent.rng.random() < 0.6:
                chosen = candidates[agent.rng.randint(0, len(candidates) - 1)]
                votes[chosen] = votes.get(chosen, 0) + 1

        if not votes:
            winner = candidates[0] if candidates else ""
            result = ElectionResult(
                winner_id=winner,
                votes_cast=0,
                total_voters=total_voters,
                turnout=0.0,
                margin=0.0,
                tick=tick,
            )
        else:
            winner = max(votes, key=votes.get)
            sorted_votes = sorted(votes.values(), reverse=True)
            margin = (sorted_votes[0] - sorted_votes[1]) / max(1, sum(sorted_votes)) \
                if len(sorted_votes) > 1 else 1.0
            result = ElectionResult(
                winner_id=winner,
                votes_cast=sum(votes.values()),
                total_voters=total_voters,
                turnout=sum(votes.values()) / max(1, total_voters),
                margin=margin,
                tick=tick,
            )

        self.results.append(result)
        return result
