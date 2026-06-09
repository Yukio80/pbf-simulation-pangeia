"""
Este modulo implementa um audit log — os eventos registram o que
aconteceu na simulacao, mas o estado autoritativo esta em memoria.
Nao e event sourcing completo (nao e possivel reconstruir o estado
apenas reproduzindo os eventos). O objetivo e rastreabilidade e
analise posterior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import Lock
from typing import List, Optional

from pangeia.persistence.event_types import Event


class AuditLog(ABC):
    @abstractmethod
    def append(self, event: Event):
        ...

    @abstractmethod
    def append_batch(self, events: List[Event]):
        ...

    @abstractmethod
    def get_events(
        self,
        tick: Optional[int] = None,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Event]:
        ...

    @abstractmethod
    def get_events_range(self, start_tick: int, end_tick: int) -> List[Event]:
        ...

    @abstractmethod
    def get_event_count(
        self,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
    ) -> int:
        ...

    @abstractmethod
    def get_latest_tick(self) -> int:
        ...

    @abstractmethod
    def close(self):
        ...


class InMemoryAuditLog(AuditLog):
    def __init__(self):
        self.events: List[Event] = []
        self._lock = Lock()

    def append(self, event: Event):
        with self._lock:
            self.events.append(event)

    def append_batch(self, events: List[Event]):
        with self._lock:
            self.events.extend(events)

    def get_events(
        self,
        tick: Optional[int] = None,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Event]:
        with self._lock:
            result = self.events
        if tick is not None:
            result = [e for e in result if e.tick == tick]
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if aggregate_type is not None:
            result = [e for e in result if e.aggregate_type == aggregate_type]
        if aggregate_id is not None:
            result = [e for e in result if e.aggregate_id == aggregate_id]
        return result[-limit - offset :][:limit] if limit else result

    def get_events_range(self, start_tick: int, end_tick: int) -> List[Event]:
        with self._lock:
            return [e for e in self.events if start_tick <= e.tick <= end_tick]

    def get_event_count(
        self,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
    ) -> int:
        with self._lock:
            result = self.events
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if aggregate_type is not None:
            result = [e for e in result if e.aggregate_type == aggregate_type]
        if aggregate_id is not None:
            result = [e for e in result if e.aggregate_id == aggregate_id]
        return len(result)

    def get_latest_tick(self) -> int:
        with self._lock:
            if not self.events:
                return 0
            return max(e.tick for e in self.events)

    def close(self):
        with self._lock:
            self.events.clear()
