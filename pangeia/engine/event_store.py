from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


class EventStore:
    """Append-only event log persistido em SQLite.

    Suporta:
    - Inserção concorrente (WAL mode)
    - Snapshots periódicos do estado completo da simulação
    - Leitura incremental (stream) a partir de um tick
    - Múltiplos processos (simulation worker + API server)
    """

    def __init__(self, path: str = ":memory:"):
        self._path = path
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                subsystem TEXT NOT NULL DEFAULT 'core',
                event_type TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL DEFAULT (julianday('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_events_tick ON events(tick);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

            CREATE TABLE IF NOT EXISTS snapshots (
                tick INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                created_at REAL NOT NULL DEFAULT (julianday('now'))
            );

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.commit()

    def append_event(self, tick: int, subsystem: str,
                     event_type: str, data: Optional[Dict] = None):
        self._conn.execute(
            "INSERT INTO events (tick, subsystem, event_type, data) VALUES (?, ?, ?, ?)",
            (tick, subsystem, event_type, json.dumps(data or {})),
        )
        self._conn.commit()

    def append_events_batch(self, events: List[Tuple[int, str, str, Dict]]):
        """Insere múltiplos eventos em uma transação."""
        self._conn.executemany(
            "INSERT INTO events (tick, subsystem, event_type, data) VALUES (?, ?, ?, ?)",
            [(t, s, e, json.dumps(d or {})) for t, s, e, d in events],
        )
        self._conn.commit()

    def get_events_since(self, tick: int, limit: int = 1000) -> List[Dict]:
        """Retorna eventos a partir de um tick (exclusive)."""
        cursor = self._conn.execute(
            "SELECT id, tick, subsystem, event_type, data FROM events WHERE tick > ? ORDER BY id LIMIT ?",
            (tick, limit),
        )
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "tick": row["tick"],
                "subsystem": row["subsystem"],
                "event_type": row["event_type"],
                "data": json.loads(row["data"]),
            })
        return results

    def stream_events(self, from_tick: int = 0,
                      batch_size: int = 100) -> Generator[List[Dict], None, None]:
        """Generator que produz lotes de eventos incrementalmente."""
        current = from_tick
        while True:
            events = self.get_events_since(current, limit=batch_size)
            if not events:
                break
            yield events
            current = events[-1]["tick"]

    def get_latest_tick(self) -> int:
        cursor = self._conn.execute(
            "SELECT COALESCE(MAX(tick), 0) as max_tick FROM events"
        )
        row = cursor.fetchone()
        return row["max_tick"] if row else 0

    def get_event_count(self) -> int:
        cursor = self._conn.execute("SELECT COUNT(*) as cnt FROM events")
        return cursor.fetchone()["cnt"]

    def save_snapshot(self, tick: int, data: Dict):
        """Salva um snapshot completo do estado da simulação."""
        self._conn.execute(
            "INSERT OR REPLACE INTO snapshots (tick, data) VALUES (?, ?)",
            (tick, json.dumps(data)),
        )
        self._conn.commit()

    def get_snapshot(self, tick: Optional[int] = None) -> Optional[Dict]:
        """Recupera o snapshot mais recente (ou de um tick específico)."""
        if tick is not None:
            cursor = self._conn.execute(
                "SELECT tick, data FROM snapshots WHERE tick = ?", (tick,)
            )
        else:
            cursor = self._conn.execute(
                "SELECT tick, data FROM snapshots ORDER BY tick DESC LIMIT 1"
            )
        row = cursor.fetchone()
        if row:
            return {"tick": row["tick"], "data": json.loads(row["data"])}
        return None

    def get_snapshot_tick_range(self) -> Optional[Tuple[int, int]]:
        """Retorna (min_tick, max_tick) dos snapshots disponíveis."""
        cursor = self._conn.execute(
            "SELECT MIN(tick) as min_t, MAX(tick) as max_t FROM snapshots"
        )
        row = cursor.fetchone()
        if row and row["min_t"] is not None:
            return (row["min_t"], row["max_t"])
        return None

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def clear(self):
        """Limpa todos os dados (útil para testes)."""
        conn = self._conn
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM snapshots")
        conn.commit()
