from __future__ import annotations

import random
from typing import Dict, List, Optional, TYPE_CHECKING

from pangeia.economy.resources import ResourceMarket
from pangeia.economy.company import Company
from pangeia.economy.indicators import EconomicIndicators
from pangeia.core.world import ResourcePool

if TYPE_CHECKING:
    from pangeia.core.agent import Agent
    from pangeia.simulation import Simulation


class Economy:
    def __init__(self, config):
        self.config = config
        self.market = ResourceMarket()
        self.companies: Dict[str, Company] = {}
        self.indicators = EconomicIndicators()
        self.total_demand = ResourcePool(0, 0, 0, 0, 0)

    def register_company(self, owner: "Agent", industry: str,
                         name: Optional[str] = None) -> Company:
        if len(self.companies) >= self.config.economy.max_companies:
            return None
        company_id = owner.agent_id + "_" + str(len(self.companies))
        company = Company(
            id=company_id,
            name=name or f"{owner.state.name} Corp",
            owner_id=owner.agent_id,
            industry=industry,
            capital=owner.state.wealth * 0.5,
        )
        self.companies[company_id] = company
        return company

    def step(self, sim: "Simulation"):
        agents = sim.agents
        world = sim.world

        self.total_demand = ResourcePool(0, 0, 0, 0, 0)
        for agent in agents.values():
            self.total_demand.energy += agent.config.agent.base_energy_consumption
            self.total_demand.food += agent.config.agent.base_food_consumption
            self.total_demand.water += agent.config.agent.base_water_consumption
            self.total_demand.compute += agent.config.agent.base_compute_cost

        self.market.update_prices(world.state.global_resources, self.total_demand)

        total_production = 0
        total_employees = 0
        for agent in agents.values():
            if not agent.state.is_alive:
                continue
            if agent.state.employer_id or agent.state.energy > 30:
                output = agent.work(1.0)
                total_production += output
                agent.state.wealth += output * 0.3

        for company in list(self.companies.values()):
            profit = company.operate(random)
            total_production += max(0, profit)

            if company.capital < -100:
                del self.companies[company.id]
                continue

            for eid in company.employees[:]:
                if eid in agents:
                    agent = agents[eid]
                    salary = 10 + company.productivity * 2
                    agent.state.wealth += salary
                    agent.state.employer_id = company.id

            total_employees += len(company.employees)

        employment_rate = total_employees / max(1, len(agents))
        self.indicators.employment = employment_rate * 0.9 + self.indicators.employment * 0.1
        self.indicators.gdp = total_production
        self.indicators.productivity = 1.0 + self.indicators.tech_level * 0.5
        self.indicators.inequality = self._calc_inequality(agents)

        wealths = [a.state.wealth for a in agents.values() if a.state.is_alive]
        if wealths:
            sorted_w = sorted(wealths)
            n = len(sorted_w)
            top10 = sum(sorted_w[int(n * 0.9):])
            bot10 = sum(sorted_w[:max(1, int(n * 0.1))])
            self.indicators.inequality = top10 / max(1, bot10 + top10) if top10 > 0 else 0.5
        self.indicators.inequality = min(1.0, self.indicators.inequality)

        self.indicators.trade_volume = sum(self.market.trade_volume.values())
        self.indicators.snapshot()

    def _calc_inequality(self, agents: Dict[str, "Agent"]) -> float:
        wealths = [a.state.wealth for a in agents.values() if a.state.is_alive]
        if len(wealths) < 2:
            return 0.3
        sorted_w = sorted(wealths)
        n = len(sorted_w)
        top10 = sum(sorted_w[int(n * 0.9):])
        total = sum(sorted_w)
        return top10 / max(1, total) if total > 0 else 0.5

    def summary(self) -> dict:
        return {
            "indicators": self.indicators.as_dict(),
            "companies": len(self.companies),
            "prices": self.market.prices.as_dict(),
        }
