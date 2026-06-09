from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.simulation import Simulation


class RelationType(Enum):
    ALLIANCE = "alliance"
    TRADE_PACT = "trade_pact"
    NEUTRAL = "neutral"
    RIVALRY = "rivalry"
    CONFLICT = "conflict"
    WAR = "war"


@dataclass
class Faction:
    id: str
    name: str
    faction_type: str
    leader_id: str
    member_ids: Set[str] = field(default_factory=set)
    power: float = 1.0
    territory_ids: List[int] = field(default_factory=list)
    resources: Dict[str, float] = field(default_factory=dict)
    created_tick: int = 0

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.faction_type,
            "leader_id": self.leader_id,
            "members": len(self.member_ids),
            "power": round(self.power, 2),
            "territories": len(self.territory_ids),
            "created_tick": self.created_tick,
        }


@dataclass
class DiplomaticRelation:
    source_id: str
    target_id: str
    relation_type: RelationType
    trust: float = 0.5
    trade_volume: float = 0.0
    duration: int = 0

    def as_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "trust": round(self.trust, 3),
            "trade_volume": round(self.trade_volume, 2),
            "duration": self.duration,
        }


class DiplomacySystem:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.factions: Dict[str, Faction] = {}
        self.relations: List[DiplomaticRelation] = []

    def register_faction(self, name: str, faction_type: str,
                         leader_id: str, tick: int) -> Faction:
        fid = f"faction_{len(self.factions)}"
        faction = Faction(
            id=fid,
            name=name,
            faction_type=faction_type,
            leader_id=leader_id,
            created_tick=tick,
            power=self.rng.uniform(0.5, 1.5),
        )
        faction.member_ids.add(leader_id)
        self.factions[fid] = faction
        return faction

    def step(self, sim: Simulation):
        tick = sim.world.state.tick
        self._maybe_form_factions(sim, tick)
        self._update_relations()
        self._resolve_conflicts(sim)

    def _maybe_form_factions(self, sim: Simulation, tick: int):
        if self.rng.random() < 0.02 and len(self.factions) < 15:
            candidates = [
                a for a in sim.agents.values()
                if a.state.is_alive and a.state.influence > 0.3
            ]
            if candidates:
                leader = self.rng.choice(candidates)
                types = ["city_state", "corporation", "religious_order",
                         "ideological_bloc", "trade_confederation"]
                ftype = self.rng.choice(types)
                names = {
                    "city_state": f"Free City of {leader.state.name}",
                    "corporation": f"{leader.state.name} Industries",
                    "religious_order": f"Order of {leader.state.name}",
                    "ideological_bloc": f"{leader.state.name} Bloc",
                    "trade_confederation": f"{leader.state.name} Trade Confederation",
                }
                faction = self.register_faction(
                    names[ftype], ftype, leader.agent_id, tick
                )
                for _ in range(self.rng.randint(2, 8)):
                    follower = self.rng.choice([
                        a for a in sim.agents.values()
                        if a.state.is_alive and a.agent_id != leader.agent_id
                    ])
                    faction.member_ids.add(follower.agent_id)
                    follower.memory.remember(
                        f"Joined faction: {faction.name}",
                        memory_type="faction", importance=0.6,
                    )
                leader.memory.remember(
                    f"Founded faction: {faction.name}",
                    memory_type="faction", importance=0.9,
                )
                sim.world.log_event(
                    "faction_formed",
                    f"Faction '{faction.name}' ({ftype}) founded by {leader.state.name}",
                    {"faction_id": faction.id, "leader": leader.agent_id},
                )

    def _update_relations(self):
        faction_list = list(self.factions.values())
        for i, f1 in enumerate(faction_list):
            for j, f2 in enumerate(faction_list):
                if i >= j:
                    continue
                existing = self._find_relation(f1.id, f2.id)
                if existing:
                    existing.duration += 1
                    existing.trust += self.rng.gauss(0, 0.01)
                    existing.trust = max(0, min(1, existing.trust))
                elif self.rng.random() < 0.05:
                    if self.rng.random() < 0.3:
                        rtype = RelationType.ALLIANCE
                    elif self.rng.random() < 0.5:
                        rtype = RelationType.RIVALRY
                    else:
                        rtype = RelationType.NEUTRAL
                    self.relations.append(DiplomaticRelation(
                        source_id=f1.id, target_id=f2.id,
                        relation_type=rtype,
                        trust=self.rng.uniform(0.2, 0.8),
                    ))

    def _find_relation(self, id1: str, id2: str) -> Optional[DiplomaticRelation]:
        for r in self.relations:
            if {r.source_id, r.target_id} == {id1, id2}:
                return r
        return None

    def _resolve_conflicts(self, sim: Simulation):
        for rel in self.relations:
            if rel.relation_type == RelationType.RIVALRY and rel.trust < 0.2:
                if self.rng.random() < 0.01:
                    rel.relation_type = RelationType.CONFLICT
                    f1 = self.factions.get(rel.source_id)
                    f2 = self.factions.get(rel.target_id)
                    if f1 and f2:
                        sim.world.log_event(
                            "conflict",
                            f"Conflict between {f1.name} and {f2.name}",
                            {"faction1": f1.id, "faction2": f2.id},
                        )
            if rel.relation_type == RelationType.ALLIANCE and rel.trust > 0.7:
                if self.rng.random() < 0.005:
                    f1 = self.factions.get(rel.source_id)
                    f2 = self.factions.get(rel.target_id)
                    if f1 and f2:
                        rel.relation_type = RelationType.TRADE_PACT
                        rel.trade_volume += self.rng.uniform(1, 10)

    def summary(self) -> dict:
        return {
            "factions": [f.as_dict() for f in self.factions.values()],
            "relations": [r.as_dict() for r in self.relations],
            "active_conflicts": sum(
                1 for r in self.relations
                if r.relation_type == RelationType.CONFLICT
            ),
            "alliances": sum(
                1 for r in self.relations
                if r.relation_type == RelationType.ALLIANCE
            ),
        }
