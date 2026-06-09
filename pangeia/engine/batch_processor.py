from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from pangeia.engine.agent_array import AgentArray, TRAIT_NAMES, _NEED_NAMES
from pangeia.core.agent import Agent
from pangeia.core.collective_memory import CollectiveMemorySystem


class BatchProcessor:
    """Operações vetorizadas sobre AgentArray.

    Substitui loops `for agent in agents` por operações numpy
    para os caminhos quentes do tick: necessidades, idade,
    alinhamento político, mutação de traços, morte.
    """

    def __init__(self, agent_array: AgentArray, rng: np.random.Generator):
        self.arr = agent_array
        self.rng = rng

    @classmethod
    def from_seed(cls, agent_array: AgentArray, seed: int) -> "BatchProcessor":
        return cls(agent_array, np.random.default_rng(seed))

    def batch_needs_decay(self, rate: float = 0.003):
        """Decaimento vetorizado: needs = max(0, needs - rate) para vivos."""
        alive = self.arr.is_alive
        for i in range(3):
            self.arr.needs[i, alive] = np.maximum(
                0.0, self.arr.needs[i, alive] - rate
            )

    def batch_needs_satisfy_by_wealth(self, wealth_threshold: float = 100,
                                       autonomy_gain: float = 0.01,
                                       competence_gain: float = 0.005,
                                       belonging_gain: float = 0.01,
                                       relationships: Optional[np.ndarray] = None):
        """Satisfaz necessidades condicionalmente."""
        alive = self.arr.is_alive
        rich = alive & (self.arr.wealth > wealth_threshold)
        self.arr.needs[0, rich] = np.minimum(1.0, self.arr.needs[0, rich] + autonomy_gain)
        self.arr.needs[1, rich] = np.minimum(1.0, self.arr.needs[1, rich] + competence_gain)

        if relationships is not None:
            social = alive & (relationships > 3)
            self.arr.needs[2, social] = np.minimum(1.0, self.arr.needs[2, social] + belonging_gain)

    def batch_age(self):
        """Incrementa idade de todos os agentes vivos."""
        self.arr.age[self.arr.is_alive] += 1

    def batch_political_drift(self, gauss_std: float = 0.005):
        """Drift político vetorizado com wealth bias."""
        alive = self.arr.is_alive
        n_alive = int(np.sum(alive))
        if n_alive == 0:
            return

        drift = self.rng.normal(0, gauss_std, size=n_alive)
        self.arr.political_alignment[alive] += drift.astype(np.float32)

        # Wealth bias
        rich = alive & (self.arr.wealth > 500)
        poor = alive & (self.arr.wealth < 20)
        self.arr.political_alignment[rich] += 0.01
        self.arr.political_alignment[poor] -= 0.01

        # Clamp
        np.clip(self.arr.political_alignment, -1.0, 1.0, out=self.arr.political_alignment)

    def batch_rebellion_drift(self, rebellion_probability: float,
                              cohort_biases: np.ndarray):
        """Drift político por rebeldia geracional."""
        alive = self.arr.is_alive
        n_alive = int(np.sum(alive))
        if n_alive == 0 or rebellion_probability <= 0.3:
            return

        effective_rp = rebellion_probability * cohort_biases[alive]
        mask = alive & (effective_rp > 0.3)
        n_mask = int(np.sum(mask))
        if n_mask == 0:
            return

        rebel_drift = self.rng.uniform(-0.03, 0.03, size=n_mask).astype(np.float32)
        rebel_drift *= effective_rp[mask].astype(np.float32)
        self.arr.political_alignment[mask] += rebel_drift
        np.clip(self.arr.political_alignment, -1.0, 1.0, out=self.arr.political_alignment)

    def batch_temperament_mutate(self, rate: float = 0.005):
        """Mutação vetorizada de traços de temperamento."""
        alive = self.arr.is_alive
        n_alive = int(np.sum(alive))
        if n_alive == 0:
            return

        # 30% dos traços de cada agente vivo sofrem mutação
        trait_mask = self.rng.random((len(TRAIT_NAMES), n_alive)) < 0.3
        deltas = self.rng.normal(0, rate, size=(len(TRAIT_NAMES), n_alive)).astype(np.float32)
        deltas[~trait_mask] = 0.0

        alive_cols = np.where(alive)[0]
        for i in range(len(TRAIT_NAMES)):
            self.arr.traits[i, alive_cols] += deltas[i]
        np.clip(self.arr.traits, 0.0, 1.0, out=self.arr.traits[:, alive_cols])

    def batch_emotional_memory_decay(self, emotional_memories_per_agent: List[int],
                                     decay_rate: float = 0.002):
        """Decaimento de intensidade das memórias emocionais.
        Note: isso ainda é O(N*M) onde M = memórias por agente,
        mas a operação de decay por memória é barata."""
        pass  # Mantido no Agent por enquanto — cada agent.emotional_memories é lista

    def batch_energy_consumption(self, consumption_rate: float = 0.1):
        """Consumo de energia vetorizado."""
        alive = self.arr.is_alive
        self.arr.energy[alive] = np.maximum(
            0.0, self.arr.energy[alive] - consumption_rate
        )

    def batch_death_check(self, min_health: float = 0.0, min_energy: float = 0.0):
        """Marca agentes mortos por saúde ou energia zerada."""
        self.arr.is_alive &= (self.arr.health > min_health)
        self.arr.is_alive &= (self.arr.energy > min_energy)

    def batch_work_output(self, base_output: float = 1.0):
        """Produção econômica vetorizada: wealth += productivity * base_output."""
        alive = self.arr.is_alive
        self.arr.wealth[alive] += self.arr.productivity[alive] * base_output

    def get_cohort_biases(self, cm: CollectiveMemorySystem) -> np.ndarray:
        """Retorna array de viés de rebeldia por coorte etária."""
        biases = np.ones(self.arr.size, dtype=np.float32)
        for i in range(self.arr.size):
            if self.arr.is_alive[i]:
                biases[i] = cm.get_cohort_rebellion_bias(int(self.arr.age[i]))
        return biases
