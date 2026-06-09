from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.core.agent import Agent


@dataclass
class Company:
    id: str
    name: str
    owner_id: str
    industry: str
    capital: float
    revenue: float = 0.0
    expenses: float = 0.0
    employees: List[str] = field(default_factory=list)
    productivity: float = 1.0
    innovation_level: float = 0.0

    def hire(self, agent_id: str) -> bool:
        if len(self.employees) < 100:
            self.employees.append(agent_id)
            return True
        return False

    def fire(self, agent_id: str) -> bool:
        if agent_id in self.employees:
            self.employees.remove(agent_id)
            return True
        return False

    def operate(self, rng: random.Random) -> float:
        output = len(self.employees) * self.productivity * (1 + self.innovation_level)
        output *= rng.uniform(0.8, 1.2)
        self.revenue += output * rng.uniform(0.9, 1.1)
        salary_cost = len(self.employees) * 10.0
        self.expenses += salary_cost + 5.0
        profit = self.revenue - self.expenses
        self.capital += profit * 0.5
        if rng.random() < 0.05:
            self.innovation_level = min(1.0, self.innovation_level + 0.01)
            self.productivity *= 1.01
        return profit

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "industry": self.industry,
            "capital": round(self.capital, 2),
            "revenue": round(self.revenue, 2),
            "expenses": round(self.expenses, 2),
            "employees": len(self.employees),
            "productivity": round(self.productivity, 3),
            "innovation": round(self.innovation_level, 3),
        }
