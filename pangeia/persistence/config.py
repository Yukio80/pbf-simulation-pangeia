from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PersistenceBackend(Enum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


@dataclass
class PersistenceConfig:
    backend: PersistenceBackend = PersistenceBackend.IN_MEMORY
    dsn: str = ""
    snapshot_interval: int = 50
    record_agent_actions: bool = False
    batch_size: int = 100

    @classmethod
    def from_env(cls) -> "PersistenceConfig":
        import os
        backend_str = os.environ.get("PANGEIA_PERSISTENCE", "in_memory")
        if backend_str == "postgres":
            dsn = os.environ.get(
                "PANGEIA_DATABASE_URL",
                "postgresql://pangeia:pangeia@localhost:5432/pangeia",
            )
            return cls(
                backend=PersistenceBackend.POSTGRES,
                dsn=dsn,
                snapshot_interval=int(os.environ.get("PANGEIA_SNAPSHOT_INTERVAL", "50")),
                record_agent_actions=os.environ.get("PANGEIA_RECORD_ACTIONS", "0") == "1",
            )
        return cls()
