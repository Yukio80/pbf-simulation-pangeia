from __future__ import annotations

from typing import Any, Dict, List, Optional

from pangeia.engine.event_store import EventStore
from pangeia.engine.simulation_worker import WorkerManager


class StateReader:
    """Leitor de estado que combina WorkerManager (último tick) e
    EventStore (persistência) para servir a API sem tocar no processo
    da simulação.
    """

    def __init__(self, store: EventStore, worker: WorkerManager):
        self._store = store
        self._worker = worker

    def _s(self, key: str, default: Any = None) -> Any:
        s = self._worker.latest_state
        if s is None:
            return default
        return s.get(key, default)

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._worker.is_alive,
            "tick": self._worker.tick,
            "time": self._s("time", 0),
            "agent_count": self._s("agent_count", 0),
            "alive_count": self._s("alive_count", 0),
            "dead_count": self._s("dead_count", 0),
        }

    def summary(self) -> Dict[str, Any]:
        s = self._worker.latest_state
        if not s:
            return {"tick": 0}
        return {
            "tick": s["tick"],
            "time": s.get("time", 0),
            "agents": {
                "total": s.get("agent_count", 0),
                "alive": s.get("alive_count", 0),
                "dead": s.get("dead_count", 0),
            },
            "world": s.get("world", {}),
            "economy": s.get("economy", {}),
            "governance": s.get("governance", {}),
            "metrics": s.get("metrics", {}),
            "culture": s.get("culture", {}),
            "technology": s.get("technology", {}),
            "diplomacy": s.get("diplomacy", {}),
            "stratification": s.get("stratification", {}),
            "history": s.get("narratives", {}),
            "collective_memory": s.get("collective_memory", {}),
            "civilization": s.get("civilization", {}),
        }

    def world(self) -> Dict:
        return self._s("world", {})

    def economy(self) -> Dict:
        return self._s("economy", {})

    def governance(self) -> Dict:
        return self._s("governance", {})

    def culture(self) -> Dict:
        return self._s("culture", {})

    def technology(self) -> Dict:
        return self._s("technology", {})

    def technology_tree(self) -> List:
        return self._s("technology_tree", [])

    def metrics(self) -> Dict:
        return self._s("metrics", {})

    def metrics_history(self, n: int = 100) -> List:
        h = self._s("metrics_history", [])
        return h[-n:]

    def world_events(self) -> List:
        return self._s("events", [])

    def civilization(self) -> Dict:
        return self._s("civilization", {})

    def narratives(self) -> Dict:
        return self._s("narratives", {})

    def narratives_timeline(self) -> List:
        return self._s("narratives_timeline", [])

    def stratification(self) -> Dict:
        return self._s("stratification", {})

    def diplomacy(self) -> Dict:
        return self._s("diplomacy", {})

    def collective_memory(self) -> Dict:
        return self._s("collective_memory", {})

    def agent_list(self, limit: int = 100, offset: int = 0) -> Dict:
        alive = self._s("alive_agents", {})
        dead = self._s("dead_agents", {})
        all_agents = {**alive, **dead}
        page = dict(list(all_agents.items())[offset:offset + limit])
        return {
            "total": len(all_agents),
            "alive": len(alive),
            "dead": len(dead),
            "agents": list(page.values()),
        }

    def agent_detail(self, agent_id: str) -> Optional[Dict]:
        alive = self._s("alive_agents", {})
        if agent_id in alive:
            return alive[agent_id]
        dead = self._s("dead_agents", {})
        return dead.get(agent_id)

    def events_since(self, tick: int, limit: int = 100) -> List[Dict]:
        return self._store.get_events_since(tick, limit=limit)
