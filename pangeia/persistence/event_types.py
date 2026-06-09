from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


class EventType:
    TICK = "tick"
    AGENT_CREATED = "agent_created"
    AGENT_DIED = "agent_died"
    AGENT_ACTION = "agent_action"
    COMPANY_CREATED = "company_created"
    COMPANY_CLOSED = "company_closed"
    ELECTION_HELD = "election_held"
    LAW_PROPOSED = "law_proposed"
    RELIGION_FOUNDED = "religion_founded"
    RELIGION_SCHISM = "religion_schism"
    IDEOLOGY_CREATED = "ideology_created"
    TECHNOLOGY_DISCOVERED = "technology_discovered"
    FACTION_CREATED = "faction_created"
    CONFLICT_STARTED = "conflict_started"
    RANDOM_EVENT_OCCURRED = "random_event_occurred"
    NARRATIVE_CREATED = "narrative_created"
    EXTERNAL_AGENT_REGISTERED = "external_agent_registered"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_STOPPED = "simulation_stopped"
    SIMULATION_RESET = "simulation_reset"
    WORLD_EVENT = "world_event"


@dataclass
class Event:
    tick: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "tick": self.tick,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "data": self.data,
            "metadata": self.metadata,
        }
