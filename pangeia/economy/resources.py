from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pangeia.core.world import ResourcePool


@dataclass
class ResourcePrice:
    energy: float = 1.0
    water: float = 0.8
    food: float = 1.2
    raw_materials: float = 1.5
    compute: float = 2.0

    def as_dict(self) -> dict:
        return {
            "energy": round(self.energy, 4),
            "water": round(self.water, 4),
            "food": round(self.food, 4),
            "raw_materials": round(self.raw_materials, 4),
            "compute": round(self.compute, 4),
        }


class ResourceMarket:
    def __init__(self):
        self.prices = ResourcePrice()
        self.price_history: List[dict] = []
        self.trade_volume: Dict[str, float] = {
            "energy": 0, "water": 0, "food": 0,
            "raw_materials": 0, "compute": 0,
        }

    def update_prices(self, global_supply: ResourcePool, demand: ResourcePool):
        for attr in ["energy", "water", "food", "raw_materials", "compute"]:
            supply_val = getattr(global_supply, attr)
            demand_val = getattr(demand, attr)
            if supply_val > 0:
                ratio = demand_val / supply_val
            else:
                ratio = 10.0
            current = getattr(self.prices, attr)
            target = current * (1.0 + (ratio - 0.5) * 0.1)
            target = max(0.01, min(100.0, target))
            new_price = current + (target - current) * 0.3
            setattr(self.prices, attr, new_price)

    def record_trade(self, resource: str, volume: float):
        if resource in self.trade_volume:
            self.trade_volume[resource] += volume

    def snapshot(self):
        entry = {
            **self.prices.as_dict(),
            "volumes": dict(self.trade_volume),
        }
        self.price_history.append(entry)
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-500:]
        return entry
