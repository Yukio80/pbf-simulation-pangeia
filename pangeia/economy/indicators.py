from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class EconomicIndicators:
    gdp: float = 0.0
    inflation: float = 0.02
    productivity: float = 1.0
    inequality: float = 0.3
    employment: float = 0.9
    tech_level: float = 0.3
    trade_volume: float = 0.0

    history: List[dict] = field(default_factory=list)

    def snapshot(self) -> dict:
        entry = self.as_dict()
        self.history.append(entry)
        if len(self.history) > 1000:
            self.history = self.history[-500:]
        return entry

    def as_dict(self) -> dict:
        return {
            "gdp": round(self.gdp, 2),
            "inflation": round(self.inflation, 4),
            "productivity": round(self.productivity, 3),
            "inequality": round(self.inequality, 4),
            "employment": round(self.employment, 4),
            "tech_level": round(self.tech_level, 3),
            "trade_volume": round(self.trade_volume, 2),
        }
