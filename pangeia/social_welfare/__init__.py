from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, TYPE_CHECKING

from pangeia.social_welfare.config import SocialWelfareConfig, GraduationMode

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class Beneficiary:
    agent_id: str
    enrolled_tick: int
    last_payout_tick: int
    total_received: float = 0.0
    school_attending: bool = True
    health_checked: bool = True
    ticks_in_program: int = 0
    graduated: bool = False
    in_transition: bool = False
    ticks_in_transition: int = 0


class SocialWelfareSystem:
    def __init__(self, config: SocialWelfareConfig):
        self.config = config
        self.beneficiaries: Dict[str, Beneficiary] = {}
        self.total_disbursed: float = 0.0
        self.total_collected: float = 0.0
        self.coverage_ratio: float = 0.0
        self.gini_before: float = 0.0
        self.gini_after: float = 0.0
        self.poverty_rate_before: float = 0.0
        self.poverty_rate_after: float = 0.0
        self.graduated_count: int = 0
        self.history: List[Dict[str, Any]] = []

    @property
    def fund_balance(self) -> float:
        return self.total_collected - self.total_disbursed

    def step(self, sim: Any, tick: int) -> None:
        alive = [a for a in sim.agents.values() if a.state.is_alive]
        if not alive:
            self._record_metrics([])
            return

        if self.config.enabled:
            self._assess_eligibility(sim, alive, tick)
            self._collect_funds(sim, alive)
            self._distribute_benefits(sim, tick)
            self._check_conditionalities(sim, alive, tick)
            self._process_graduation(tick)

        self._record_metrics(alive)

    def _assess_eligibility(
        self, sim: Any, agents: List[Agent], tick: int
    ) -> None:
        max_beneficiaries = int(len(agents) * self.config.max_beneficiaries_ratio)
        candidates = [
            a for a in agents
            if a.state.wealth < self.config.eligibility_threshold
            and a.agent_id not in self.beneficiaries
        ]
        candidates.sort(key=lambda a: a.state.wealth)
        new_slots = max(0, max_beneficiaries - len(self.beneficiaries))
        for agent in candidates[:new_slots]:
            self.beneficiaries[agent.agent_id] = Beneficiary(
                agent_id=agent.agent_id,
                enrolled_tick=tick,
                last_payout_tick=tick,
            )

    def _collect_funds(self, sim: Any, agents: List[Agent]) -> None:
        total_collected = 0.0
        for agent in agents:
            if agent.state.wealth > self.config.eligibility_threshold * 2:
                surcharge = agent.state.wealth * self.config.funding_tax_surcharge
                agent.state.wealth -= surcharge
                total_collected += surcharge
        self.total_collected += total_collected

    def _distribute_benefits(self, sim: Any, tick: int) -> None:
        tick_disbursed = 0.0
        for agent_id, beneficiary in self.beneficiaries.items():
            payout = self._effective_payout(beneficiary)
            if payout <= 0:
                continue
            beneficiary.total_received += payout
            beneficiary.last_payout_tick = tick
            beneficiary.ticks_in_program += 1
            tick_disbursed += payout
            agent = sim.agents.get(agent_id)
            if agent:
                agent.state.wealth += payout
        self.total_disbursed += tick_disbursed

    def _effective_payout(self, ben: Beneficiary) -> float:
        if ben.in_transition:
            remaining = 1.0 - (
                ben.ticks_in_transition * self.config.graduation_transition_band
            )
            return max(0.0, self.config.benefit_per_capita * remaining)
        return self.config.benefit_per_capita

    def _check_conditionalities(
        self, sim: Any, agents: List[Agent], tick: int
    ) -> None:
        if not self.config.conditionalities_enabled:
            return
        for agent in agents:
            if agent.agent_id not in self.beneficiaries:
                continue
            ben = self.beneficiaries[agent.agent_id]
            if self.config.condition_school_attendance:
                has_education = (
                    getattr(agent.state, 'skills', {}).get('education', 0) > 0.3
                    if hasattr(agent.state, 'skills')
                    else (tick - ben.enrolled_tick) < 5
                )
                ben.school_attending = has_education
            if self.config.condition_health_checkup:
                ben.health_checked = getattr(agent.state, 'health', 50) > 30

    def _process_graduation(self, tick: int) -> None:
        graduated: List[str] = []
        for agent_id, ben in self.beneficiaries.items():
            if ben.ticks_in_program < self.config.graduation_grace_ticks:
                continue

            if self.config.graduation_mode == GraduationMode.ABRUPT:
                graduated.append(agent_id)

            elif self.config.graduation_mode == GraduationMode.GRADUAL:
                if not ben.in_transition:
                    ben.in_transition = True
                    ben.ticks_in_transition = 0
                ben.ticks_in_transition += 1
                if self._effective_payout(ben) <= 0:
                    graduated.append(agent_id)

        for agent_id in graduated:
            self.beneficiaries[agent_id].graduated = True
            del self.beneficiaries[agent_id]
            self.graduated_count += 1

    def _record_metrics(self, agents: List[Agent]) -> None:
        if not agents:
            self.gini_before = 0.0
            self.gini_after = 0.0
            self.poverty_rate_before = 0.0
            self.poverty_rate_after = 0.0
            self.coverage_ratio = 0.0
            return
        wealths = [a.state.wealth for a in agents]
        self.gini_before = self._gini(wealths)

        if self.config.enabled:
            post_wealth = list(wealths)
            for agent in agents:
                if agent.agent_id in self.beneficiaries:
                    idx = next(
                        i for i, a in enumerate(agents) if a.agent_id == agent.agent_id
                    )
                    post_wealth[idx] += self._effective_payout(
                        self.beneficiaries[agent.agent_id]
                    )
            self.gini_after = self._gini(post_wealth)

            pov_line = self.config.eligibility_threshold
            before_poor = sum(1 for w in wealths if w < pov_line)
            after_poor = sum(1 for w in post_wealth if w < pov_line)
            total = len(agents)
            self.poverty_rate_before = before_poor / total if total else 0
            self.poverty_rate_after = after_poor / total if total else 0
            self.coverage_ratio = len(self.beneficiaries) / total if total else 0
        else:
            self.gini_after = self.gini_before
            total = len(agents)
            pov_line = self.config.eligibility_threshold
            poor = sum(1 for w in wealths if w < pov_line)
            self.poverty_rate_before = poor / total if total else 0
            self.poverty_rate_after = poor / total if total else 0
            self.coverage_ratio = 0.0

    def _gini(self, values: List[float]) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        s = sum(sorted_vals)
        if s == 0:
            return 0.0
        cumsum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
        return (2 * cumsum) / (n * s) - (n + 1) / n

    def summary(self) -> Dict[str, Any]:
        return {
            "enabled": self.config.enabled,
            "active_beneficiaries": len(self.beneficiaries),
            "total_disbursed": round(self.total_disbursed, 2),
            "total_collected": round(self.total_collected, 2),
            "fund_balance": round(self.fund_balance, 2),
            "coverage_ratio": round(self.coverage_ratio, 4),
            "gini_before": round(self.gini_before, 4),
            "gini_after": round(self.gini_after, 4),
            "poverty_rate_before": round(self.poverty_rate_before, 4),
            "poverty_rate_after": round(self.poverty_rate_after, 4),
            "graduated_count": self.graduated_count,
            "benefit_per_capita": self.config.benefit_per_capita,
            "eligibility_threshold": self.config.eligibility_threshold,
        }
