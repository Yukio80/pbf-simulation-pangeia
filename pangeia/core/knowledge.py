from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class Belief:
    proposition: str
    confidence: float
    truth_value: Optional[bool]
    source: str
    timestamp: float
    category: str = "general"
    spread_count: int = 0

    def decay(self, current_time: float, decay_rate: float = 0.0005):
        age = current_time - self.timestamp
        self.confidence = max(0.0, self.confidence - decay_rate * age)

    def as_dict(self) -> dict:
        return {
            "proposition": self.proposition,
            "confidence": round(self.confidence, 3),
            "truth_value": self.truth_value,
            "source": self.source,
            "category": self.category,
            "spread_count": self.spread_count,
        }


class KnowledgeBase:
    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self.beliefs: Dict[str, Belief] = {}
        self.secret_knowledge: Dict[str, Belief] = {}
        self.local_knowledge: Dict[str, Belief] = {}

    def add_belief(self, proposition: str, confidence: float,
                   source: str, category: str = "general",
                   truth_value: Optional[bool] = None,
                   secret: bool = False):
        belief = Belief(
            proposition=proposition,
            confidence=max(0.0, min(1.0, confidence)),
            truth_value=truth_value,
            source=source,
            timestamp=time.time(),
            category=category,
        )
        if secret:
            self.secret_knowledge[proposition] = belief
        else:
            self.beliefs[proposition] = belief
        self._trim()

    def add_shared_knowledge(self, proposition: str, confidence: float,
                             source: str, category: str = "general",
                             truth_value: Optional[bool] = None):
        if proposition not in self.beliefs:
            self.add_belief(proposition, confidence, source, category, truth_value)
        else:
            existing = self.beliefs[proposition]
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.source = source
                existing.timestamp = time.time()

    def get_belief(self, proposition: str) -> Optional[Belief]:
        return self.beliefs.get(proposition)

    def query(self, category: Optional[str] = None,
              min_confidence: float = 0.0) -> List[Belief]:
        results = []
        for belief in self.beliefs.values():
            if category and belief.category != category:
                continue
            if belief.confidence < min_confidence:
                continue
            results.append(belief)
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    def validate_information(self, proposition: str,
                             other_sources: List["KnowledgeBase"]) -> float:
        if proposition not in self.beliefs:
            return 0.0
        own = self.beliefs[proposition]
        agreements = 0
        total = 0
        for kb in other_sources:
            other = kb.get_belief(proposition)
            if other:
                total += 1
                if abs(other.confidence - own.confidence) < 0.3:
                    agreements += 1
        return agreements / max(1, total)

    def _trim(self):
        total = len(self.beliefs)
        if total > self.max_items:
            sorted_beliefs = sorted(self.beliefs.values(), key=lambda x: x.confidence)
            for b in sorted_beliefs[:total - self.max_items]:
                del self.beliefs[b.proposition]

    def summarize(self) -> dict:
        return {
            "beliefs": len(self.beliefs),
            "secret": len(self.secret_knowledge),
            "local": len(self.local_knowledge),
            "categories": list(set(b.category for b in self.beliefs.values())),
        }
