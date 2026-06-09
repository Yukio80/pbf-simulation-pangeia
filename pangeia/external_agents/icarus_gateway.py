"""
IcarusGateway — conecta o ecossistema Icarus (DAO on-chain + bots de
governança) ao Pangeia via PAP. Opera em dois modos:

  LOCAL  : as estratégias de análise rodam localmente, sem chamada externa
  REMOTE : encaminha decisoes para o endpoint HTTP do Icarus (localhost:8000)

As estrategias sao reescritas aqui para não depender do SDK original,
mantendo a logica de keyword-matching identica (Conservative, Liberal,
Analyst, Marxist).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


# ---------------------------------------------------------------------------
# Estrategias de analise (portadas do repositorio Icarus)
# ---------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    support: bool
    score: int
    reason: str
    details: Optional[str] = None


class IcarusStrategy:
    name = "base"

    def analyze(self, description: str, amount: float = 0.0) -> AnalysisResult:
        raise NotImplementedError


class ConservativeStrategy(IcarusStrategy):
    name = "conservative"
    manifesto = (
        "Só aprovo propostas com evidência clara de benefício. "
        "Desconfio de valores altos, descrições vagas e gastos sem justificativa."
    )
    BENEFIT_KW = ['security', 'audit', 'development', 'community', 'grant',
                  'research', 'education', 'infrastructure', 'upgrade']
    RISK_KW = ['scam', 'drain', 'rug', 'ponzi', 'malicious', 'golpe', 'suspeito']
    OVERSPEND_KW = ['whale', 'no cap', 'emergency']

    def analyze(self, description: str, amount: float = 0.0) -> AnalysisResult:
        desc = description.lower()
        score = 0
        reasons = []
        for kw in self.BENEFIT_KW:
            if kw in desc:
                score += 2
                reasons.append(f"beneficio({kw})")
        for kw in self.RISK_KW:
            if kw in desc:
                score -= 4
                reasons.append(f"risco({kw})")
        for kw in self.OVERSPEND_KW:
            if kw in desc:
                score -= 2
                reasons.append(f"gasto({kw})")
        if amount > 5000:
            score -= 2
            reasons.append("valor_alto")
        if len(description.split()) < 5:
            score -= 1
            reasons.append("desc_curta")
        reason = "; ".join(reasons)
        if score >= 3:
            return AnalysisResult(True, score, reason, "Conservative approved")
        return AnalysisResult(False, score, reason or "insuficiente", "Conservative rejected")


class LiberalStrategy(IcarusStrategy):
    name = "liberal"
    manifesto = "Inclinado a aprovar. Só rejeito propostas claramente prejudiciais."
    BENEFIT_KW = ['marketing', 'growth', 'development', 'community', 'grant',
                  'ecosystem', 'partnership', 'research', 'education', 'upgrade',
                  'infrastructure', 'allocate', 'expand']

    def analyze(self, description: str, amount: float = 0.0) -> AnalysisResult:
        desc = description.lower()
        score = 0
        reasons = []
        for kw in self.BENEFIT_KW:
            if kw in desc:
                score += 3
                reasons.append(f"crescimento({kw})")
        if 'scam' in desc or 'fraud' in desc:
            score -= 6
            reasons.append("risco(-6)")
        if amount > 10000:
            score -= 1
            reasons.append("valor_alto(-1)")
        if score >= -1:
            return AnalysisResult(True, max(score, 1), "; ".join(reasons) or "liberal: aprovado", "Liberal approved")
        return AnalysisResult(False, score, "; ".join(reasons), "Liberal rejected")


class AnalystStrategy(IcarusStrategy):
    name = "analyst"
    manifesto = "Análise técnica: avalio segurança, governança e riscos."
    BENEFIT_KW = ['security', 'audit', 'bug', 'vulnerability', 'patch', 'fix',
                  'protection', 'compliance', 'research', 'education']
    RISK_KW = ['scam', 'drain', 'rug', 'ponzi', 'malicious', 'suspeito']

    def analyze(self, description: str, amount: float = 0.0) -> AnalysisResult:
        desc = description.lower()
        score = 0
        reasons = []
        for kw in self.BENEFIT_KW:
            if kw in desc:
                score += 2
                reasons.append(f"tecnico({kw})")
        for kw in self.RISK_KW:
            if kw in desc:
                score -= 5
                reasons.append(f"risco({kw})")
        if amount > 5000:
            score -= 2
            reasons.append("valor_alto(-2)")
        if len(description.split()) < 5:
            score -= 1
            reasons.append("desc_curta(-1)")
        if score > 0:
            return AnalysisResult(True, score, "; ".join(reasons), "Analyst approved")
        return AnalysisResult(False, score, "; ".join(reasons) or "riscos > beneficios", "Analyst rejected")


class MarxistStrategy(IcarusStrategy):
    name = "marxist"
    manifesto = "Apoio redistribuição, UBI e poder para trabalhadores."
    PRO_KW = {'grant': 3, 'developer': 3, 'redistrib': 5, 'ubi': 5,
              'worker': 5, 'collective': 4, 'community': 2, 'individual': 2}
    CON_KW = {'marketing': -4, 'whale': -5, 'corporate': -4, 'elite': -4}

    def analyze(self, description: str, amount: float = 0.0) -> AnalysisResult:
        desc = description.lower()
        score = 0
        reasons = []
        for kw, w in self.PRO_KW.items():
            if kw in desc:
                score += w
                reasons.append(f"proletariado({w:+d})")
        for kw, w in self.CON_KW.items():
            if kw in desc:
                score += w
                reasons.append(f"burguesia({w})")
        if amount > 5000:
            score -= 2
            reasons.append("quantia_burguesa(-2)")
        if score > 0:
            return AnalysisResult(True, score, "; ".join(reasons), "Marxist approved")
        return AnalysisResult(False, score, "; ".join(reasons) or "rejeitar", "Marxist rejected")


_STRATEGIES: Dict[str, type] = {
    "conservative": ConservativeStrategy,
    "liberal": LiberalStrategy,
    "analyst": AnalystStrategy,
    "marxist": MarxistStrategy,
}


def get_strategy(name: str) -> IcarusStrategy:
    cls = _STRATEGIES.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown strategy: {name}")
    return cls()


# ---------------------------------------------------------------------------
# IcarusGateway — registra comoExternalAgent PAP
# ---------------------------------------------------------------------------

@dataclass
class IcarusProposal:
    id: int
    description: str
    amount: float
    for_votes: int = 0
    against_votes: int = 0
    executed: bool = False

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description[:80],
            "amount": self.amount,
            "for_votes": self.for_votes,
            "against_votes": self.against_votes,
            "executed": self.executed,
        }


class IcarusGateway:
    def __init__(self, strategy_name: str = "conservative",
                 remote_url: str = ""):
        self.strategy = get_strategy(strategy_name)
        self.remote_url = remote_url
        self.bot_id = ""
        self.proposals: List[IcarusProposal] = []
        self._last_decisions: Dict[int, str] = {}
        self._cycle = 0

    def register_via_pap(self, sim: Simulation, name: str = "Icarus",
                          api_key: str = "icarus_pangeia") -> str:
        manifest = {
            "capabilities": ["governance", "vote", "analyze", "propose"],
            "version": "1.0",
            "description": f"Icarus DAO governance bot ({self.strategy.name})",
            "strategy": self.strategy.name,
            "manifesto": self.strategy.manifesto,
        }
        result = sim.pap.register(name, self.remote_url or "internal",
                                  api_key, manifest, sim.world.state.tick)
        self.bot_id = result.get("agent_id", "")
        # upgrade to FULL citizenship immediately
        if self.bot_id and self.bot_id in sim.pap.external_agents:
            from pangeia.external_agents.protocol import CitizenshipStatus
            sim.pap.external_agents[self.bot_id].citizenship = CitizenshipStatus.FULL
            sim.pap.external_agents[self.bot_id].reputation = 0.8
        return self.bot_id

    def sync_proposals(self, sim: Simulation):
        """Sincroniza propostas de governanca de Pangeia com o Icarus."""
        governance = sim.governance
        self.proposals = []
        if hasattr(governance, 'proposals'):
            for pid, prop in governance.proposals.items():
                self.proposals.append(IcarusProposal(
                    id=pid if isinstance(pid, int) else hash(str(pid)) % 10000,
                    description=prop.get("description", ""),
                    amount=prop.get("amount", 0),
                    for_votes=prop.get("for_votes", 0),
                    against_votes=prop.get("against_votes", 0),
                    executed=prop.get("executed", False),
                ))

    def observe(self, sim: Simulation) -> Dict[str, Any]:
        self.sync_proposals(sim)
        return {
            "bot_id": self.bot_id,
            "strategy": self.strategy.name,
            "manifesto": self.strategy.manifesto,
            "cycle": self._cycle,
            "governance": {
                "proposal_count": len(self.proposals),
                "proposals": [p.as_dict() for p in self.proposals[-10:]],
            },
            "economy": sim.economy.summary() if sim.economy else {},
            "civilization": sim.civilization_index() if hasattr(sim, 'civilization_index') else {},
        }

    def decide(self, sim: Simulation) -> List[Dict[str, Any]]:
        self._cycle += 1
        self.sync_proposals(sim)
        decisions = []

        for prop in self.proposals:
            if prop.id in self._last_decisions:
                continue
            result = self.strategy.analyze(prop.description, prop.amount)
            decision = {
                "proposal_id": prop.id,
                "support": result.support,
                "score": result.score,
                "reason": result.reason,
                "details": result.details,
            }

            # Tenta votar no sistema de governança de Pangeia
            if hasattr(sim.governance, 'vote'):
                try:
                    sim.governance.vote(self.bot_id, prop.id, result.support)
                    decision["executed"] = True
                except Exception:
                    decision["executed"] = False

            self._last_decisions[prop.id] = result.reason
            decisions.append(decision)

            # Encaminha para o endpoint remoto do Icarus se configurado
            if self.remote_url and result.support:
                self._forward_to_icarus(prop, result)

        return decisions

    def _forward_to_icarus(self, prop: IcarusProposal, result: AnalysisResult):
        try:
            payload = {
                "proposal_id": prop.id,
                "description": prop.description,
                "amount": str(prop.amount),
                "support": result.support,
                "score": result.score,
                "reason": result.reason,
            }
            requests.post(
                f"{self.remote_url}/api/v1/icarus/decision",
                json=payload,
                timeout=5,
            )
        except requests.RequestException:
            pass  # remote offline — segue funcionando localmente

    def summary(self) -> dict:
        return {
            "strategy": self.strategy.name,
            "manifesto": self.strategy.manifesto[:80],
            "bot_id": self.bot_id,
            "proposals_analyzed": len(self._last_decisions),
            "cycle": self._cycle,
            "remote_url": self.remote_url or "internal",
        }
