from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent
    from pangeia.governance.government import Law


class LawSystem:
    def __init__(self):
        self.pending_laws: List[Law] = []

    def propose(self, law: Law):
        self.pending_laws.append(law)

    def vote_on_law(self, law: Law, agents: Dict[str, "Agent"]) -> bool:
        votes_for = 0
        votes_against = 0
        total = 0
        for agent in agents.values():
            if not agent.state.is_alive:
                continue
            total += 1
            support = agent.rng.random()
            alignment_effect = abs(agent.state.political_alignment) * 0.2
            if support > 0.5 + alignment_effect:
                votes_for += 1
            else:
                votes_against += 1

        law.votes_for = votes_for
        law.votes_against = votes_against
        passed = votes_for > votes_against and total > 0
        law.active = passed
        law.support = votes_for / max(1, total)

        if passed:
            self.pending_laws = [l for l in self.pending_laws if l.id != law.id]

        return passed
