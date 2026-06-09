from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from pangeia.core.agent import Agent
from pangeia.core.psychology import TRAIT_NAMES, ArchetypeType

# Index mapping for archetypes
_ARCHETYPE_NAMES = [at.value for at in ArchetypeType]
_ARCHETYPE_TO_IDX = {name: i for i, name in enumerate(_ARCHETYPE_NAMES)}
_ARCHETYPE_COUNT = len(_ARCHETYPE_NAMES)

# Index mapping for emotions
_EMOTION_NAMES = ["happiness", "trust", "anger", "fear", "curiosity", "sadness"]
_EMOTION_TO_IDX = {name: i for i, name in enumerate(_EMOTION_NAMES)}

# Index mapping for needs
_NEED_NAMES = ["autonomy", "competence", "belonging"]
_NEED_TO_IDX = {name: i for i, name in enumerate(_NEED_NAMES)}


class AgentArray:
    """Camada de dados contígua (numpy) para operações vetorizadas.

    Mantém arrays paralelos para todos os agentes vivos.
    Cada coluna = 1 agente. Operações em batches evitam
    loops Python sobre agentes individuais.

    A classe Agent continua existindo como fachada para lógica
    complexa (decide, memória, social), mas o estado numérico
    quente (riqueza, traços, emoções, necessidades) vive aqui.
    """

    def __init__(self, agents: Optional[Dict[str, Agent]] = None):
        self.agent_ids: np.ndarray = np.array([], dtype='U32')
        self.size: int = 0
        self.capacity: int = 0

        # Númericos — shape (N,) salvo indicação contrária
        self.archetypes: np.ndarray = np.array([], dtype=np.int8)
        self.wealth: np.ndarray = np.array([], dtype=np.float32)
        self.influence: np.ndarray = np.array([], dtype=np.float32)
        self.age: np.ndarray = np.array([], dtype=np.int32)
        self.is_alive: np.ndarray = np.array([], dtype=bool)
        self.energy: np.ndarray = np.array([], dtype=np.float32)
        self.health: np.ndarray = np.array([], dtype=np.float32)
        self.political_alignment: np.ndarray = np.array([], dtype=np.float32)
        self.education: np.ndarray = np.array([], dtype=np.float32)
        self.productivity: np.ndarray = np.array([], dtype=np.float32)
        self.territory_id: np.ndarray = np.array([], dtype=np.int32)

        # Traços de temperamento — shape (11, N)
        self.traits: np.ndarray = np.zeros((len(TRAIT_NAMES), 0), dtype=np.float32)

        # Emoções — shape (6, N)
        self.emotions: np.ndarray = np.zeros((len(_EMOTION_NAMES), 0), dtype=np.float32)

        # Necessidades — shape (3, N)
        self.needs: np.ndarray = np.zeros((len(_NEED_NAMES), 0), dtype=np.float32)

        if agents:
            self.sync_from_agents(agents)

    def sync_from_agents(self, agents: Dict[str, Agent]):
        """(Re)popula todos os arrays a partir do dicionário de agentes."""
        n = len(agents)
        self.capacity = n
        self.size = n

        ids = list(agents.keys())
        self.agent_ids = np.array(ids, dtype='U32')

        self.archetypes = np.array([
            _ARCHETYPE_TO_IDX.get(a.archetype.archetype_type.value, 0)
            for a in agents.values()
        ], dtype=np.int8)

        self.wealth = np.array([a.state.wealth for a in agents.values()], dtype=np.float32)
        self.influence = np.array([a.state.influence for a in agents.values()], dtype=np.float32)
        self.age = np.array([a.state.age for a in agents.values()], dtype=np.int32)
        self.is_alive = np.array([a.state.is_alive for a in agents.values()], dtype=bool)
        self.energy = np.array([a.state.energy for a in agents.values()], dtype=np.float32)
        self.health = np.array([a.state.health for a in agents.values()], dtype=np.float32)
        self.political_alignment = np.array(
            [a.state.political_alignment for a in agents.values()], dtype=np.float32
        )
        self.education = np.array([a.state.education_level for a in agents.values()], dtype=np.float32)
        self.productivity = np.array([a.state.productivity for a in agents.values()], dtype=np.float32)
        self.territory_id = np.array(
            [a.state.territory_id or -1 for a in agents.values()], dtype=np.int32
        )

        # Traits: shape (11, N)
        traits_list = []
        for a in agents.values():
            td = a.temperament.as_dict()
            traits_list.append([td[name] for name in TRAIT_NAMES])
        self.traits = np.array(traits_list, dtype=np.float32).T

        # Emotions: shape (6, N)
        emo_list = []
        for a in agents.values():
            ed = a.emotions.as_dict()
            emo_list.append([ed[name] for name in _EMOTION_NAMES])
        self.emotions = np.array(emo_list, dtype=np.float32).T

        # Needs: shape (3, N)
        needs_list = []
        for a in agents.values():
            nd = a.needs.as_dict()
            needs_list.append([nd[name] for name in _NEED_NAMES])
        self.needs = np.array(needs_list, dtype=np.float32).T

        # Build index
        self._id_to_idx = {aid: i for i, aid in enumerate(ids)}

    def sync_to_agents(self, agents: Dict[str, Agent]):
        """Escreve de volta dos arrays para os objetos Agent."""
        for aid, agent in agents.items():
            idx = self._id_to_idx.get(aid)
            if idx is None:
                continue
            agent.state.wealth = float(self.wealth[idx])
            agent.state.influence = float(self.influence[idx])
            agent.state.age = int(self.age[idx])
            agent.state.is_alive = bool(self.is_alive[idx])
            agent.state.energy = float(self.energy[idx])
            agent.state.health = float(self.health[idx])
            agent.state.political_alignment = float(self.political_alignment[idx])
            agent.state.education_level = float(self.education[idx])
            agent.state.productivity = float(self.productivity[idx])

    def alive_mask(self) -> np.ndarray:
        return self.is_alive

    def alive_count(self) -> int:
        return int(np.sum(self.is_alive))

    def alive_indices(self) -> np.ndarray:
        return np.where(self.is_alive)[0]

    def wealth_slice(self) -> np.ndarray:
        return self.wealth

    def age_slice(self) -> np.ndarray:
        return self.age

    def get_idx(self, agent_id: str) -> Optional[int]:
        return self._id_to_idx.get(agent_id)

    def add_agent(self, agent: Agent) -> int:
        """Adiciona um novo agente aos arrays. Retorna o índice."""
        idx = self.size
        if idx >= self.capacity:
            self._grow(max(1, self.capacity * 2))
        self._set_agent(idx, agent)
        self.size += 1
        self._id_to_idx[agent.agent_id] = idx
        return idx

    def remove_agent(self, agent_id: str):
        idx = self._id_to_idx.pop(agent_id, None)
        if idx is None:
            return
        # Swap with last
        last_idx = self.size - 1
        if idx != last_idx:
            self._swap(idx, last_idx)
            self._id_to_idx[self.agent_ids[idx]] = idx
        self.size -= 1
        self.is_alive[self.size] = False

    def _grow(self, new_capacity: int):
        old = self.capacity
        self.capacity = new_capacity
        for field in ("agent_ids", "archetypes", "wealth", "influence", "age",
                       "is_alive", "energy", "health", "political_alignment",
                       "education", "productivity", "territory_id"):
            arr = getattr(self, field)
            if len(arr) < new_capacity:
                setattr(self, field, np.pad(arr, (0, new_capacity - len(arr)),
                                            constant_values=0))
        for field in ("traits", "emotions", "needs"):
            arr = getattr(self, field)
            if arr.shape[1] < new_capacity:
                pad_width = ((0, 0), (0, new_capacity - arr.shape[1]))
                setattr(self, field, np.pad(arr, pad_width, constant_values=0))

    def _set_agent(self, idx: int, agent: Agent):
        self.agent_ids[idx] = agent.agent_id
        td = agent.temperament.as_dict()
        for i, name in enumerate(TRAIT_NAMES):
            self.traits[i, idx] = td[name]
        ed = agent.emotions.as_dict()
        for i, name in enumerate(_EMOTION_NAMES):
            self.emotions[i, idx] = ed[name]
        nd = agent.needs.as_dict()
        for i, name in enumerate(_NEED_NAMES):
            self.needs[i, idx] = nd[name]
        self.archetypes[idx] = _ARCHETYPE_TO_IDX.get(
            agent.archetype.archetype_type.value, 0
        )
        self.wealth[idx] = agent.state.wealth
        self.influence[idx] = agent.state.influence
        self.age[idx] = agent.state.age
        self.is_alive[idx] = agent.state.is_alive
        self.energy[idx] = agent.state.energy
        self.health[idx] = agent.state.health
        self.political_alignment[idx] = agent.state.political_alignment
        self.education[idx] = agent.state.education_level
        self.productivity[idx] = agent.state.productivity
        self.territory_id[idx] = agent.state.territory_id or -1

    def _swap(self, i: int, j: int):
        for field in ("agent_ids", "archetypes", "wealth", "influence", "age",
                       "is_alive", "energy", "health", "political_alignment",
                       "education", "productivity", "territory_id"):
            arr = getattr(self, field)
            arr[i], arr[j] = arr[j], arr[i]
        for field in ("traits", "emotions", "needs"):
            arr = getattr(self, field)
            arr[:, i], arr[:, j] = arr[:, j].copy(), arr[:, i].copy()

    def summary(self) -> dict:
        alive = self.alive_count()
        if alive == 0:
            return {"size": 0, "alive": 0}
        return {
            "size": self.size,
            "alive": alive,
            "avg_wealth": float(np.mean(self.wealth[self.is_alive])),
            "median_wealth": float(np.median(self.wealth[self.is_alive])),
            "gini": float(self._gini(self.wealth[self.is_alive])),
            "avg_age": float(np.mean(self.age[self.is_alive])),
            "avg_influence": float(np.mean(self.influence[self.is_alive])),
            "total_wealth": float(np.sum(self.wealth[self.is_alive])),
        }

    @staticmethod
    def _gini(arr: np.ndarray) -> float:
        if len(arr) == 0 or np.sum(arr) == 0:
            return 0.0
        sorted_arr = np.sort(arr)
        n = len(sorted_arr)
        cumsum = np.cumsum(sorted_arr)
        return float((2 * np.sum((np.arange(1, n + 1) * sorted_arr)) -
                      (n + 1) * np.sum(sorted_arr)) / (n * np.sum(sorted_arr)))
