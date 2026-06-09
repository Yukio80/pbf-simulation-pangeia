from __future__ import annotations

import json
from threading import Lock
from typing import Dict, List, Optional, Any

from pangeia.persistence.event_types import Event
from pangeia.persistence.event_store import AuditLog


class PostgresAuditLog(AuditLog):
    def __init__(self, dsn: str, auto_create_tables: bool = True):
        self.dsn = dsn
        self._lock = Lock()
        self._conn = None
        if auto_create_tables:
            self._init_tables()

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            import psycopg2
            self._conn = psycopg2.connect(self.dsn)
            self._conn.autocommit = False
        return self._conn

    def _init_tables(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pangeia_events (
                        id BIGSERIAL PRIMARY KEY,
                        tick INTEGER NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        aggregate_type VARCHAR(50) NOT NULL,
                        aggregate_id VARCHAR(100) NOT NULL,
                        data JSONB NOT NULL,
                        metadata JSONB DEFAULT '{}',
                        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pe_tick ON pangeia_events(tick)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pe_type ON pangeia_events(event_type)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pe_agg ON pangeia_events(aggregate_type, aggregate_id)")

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pangeia_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        tick INTEGER NOT NULL,
                        snapshot_type VARCHAR(50) NOT NULL,
                        state JSONB NOT NULL,
                        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_ps_tick ON pangeia_snapshots(tick)")
            conn.commit()
        finally:
            pass

    def append(self, event: Event):
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pangeia_events (tick, event_type, aggregate_type, aggregate_id, data, metadata) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    event.tick,
                    event.event_type,
                    event.aggregate_type,
                    event.aggregate_id,
                    json.dumps(event.data),
                    json.dumps(event.metadata),
                ),
            )
            conn.commit()

    def append_batch(self, events: List[Event]):
        if not events:
            return
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            rows = [
                (
                    e.tick,
                    e.event_type,
                    e.aggregate_type,
                    e.aggregate_id,
                    json.dumps(e.data),
                    json.dumps(e.metadata),
                )
                for e in events
            ]
            cur.executemany(
                "INSERT INTO pangeia_events (tick, event_type, aggregate_type, aggregate_id, data, metadata) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                rows,
            )
            conn.commit()

    def _query(
        self,
        tick=None,
        event_type=None,
        aggregate_type=None,
        aggregate_id=None,
        limit=1000,
        offset=0,
    ) -> List[Event]:
        conn = self._get_conn()
        conditions = []
        params = []
        if tick is not None:
            conditions.append("tick = %s")
            params.append(tick)
        if event_type is not None:
            conditions.append("event_type = %s")
            params.append(event_type)
        if aggregate_type is not None:
            conditions.append("aggregate_type = %s")
            params.append(aggregate_type)
        if aggregate_id is not None:
            conditions.append("aggregate_id = %s")
            params.append(aggregate_id)

        where = " AND ".join(conditions) if conditions else "TRUE"
        query = (
            f"SELECT tick, event_type, aggregate_type, aggregate_id, data, metadata "
            f"FROM pangeia_events WHERE {where} "
            f"ORDER BY id DESC LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return [
            Event(
                tick=r[0],
                event_type=r[1],
                aggregate_type=r[2],
                aggregate_id=r[3],
                data=r[4],
                metadata=r[5],
            )
            for r in rows
        ][::-1]

    def get_events(
        self,
        tick=None,
        event_type=None,
        aggregate_type=None,
        aggregate_id=None,
        limit=1000,
        offset=0,
    ) -> List[Event]:
        with self._lock:
            return self._query(
                tick=tick,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                limit=limit,
                offset=offset,
            )

    def get_events_range(self, start_tick: int, end_tick: int) -> List[Event]:
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            cur.execute(
                "SELECT tick, event_type, aggregate_type, aggregate_id, data, metadata "
                "FROM pangeia_events WHERE tick >= %s AND tick <= %s "
                "ORDER BY id ASC",
                (start_tick, end_tick),
            )
            rows = cur.fetchall()
        return [
            Event(tick=r[0], event_type=r[1], aggregate_type=r[2],
                  aggregate_id=r[3], data=r[4], metadata=r[5])
            for r in rows
        ]

    def get_event_count(self, event_type=None, aggregate_type=None, aggregate_id=None) -> int:
        conn = self._get_conn()
        conditions = []
        params = []
        if event_type is not None:
            conditions.append("event_type = %s")
            params.append(event_type)
        if aggregate_type is not None:
            conditions.append("aggregate_type = %s")
            params.append(aggregate_type)
        if aggregate_id is not None:
            conditions.append("aggregate_id = %s")
            params.append(aggregate_id)
        where = " AND ".join(conditions) if conditions else "TRUE"
        with self._lock, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM pangeia_events WHERE {where}", params)
            return cur.fetchone()[0]

    def get_latest_tick(self) -> int:
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(tick), 0) FROM pangeia_events")
            return cur.fetchone()[0]

    def save_snapshot(self, tick: int, snapshot_type: str, state: dict):
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pangeia_snapshots (tick, snapshot_type, state) VALUES (%s, %s, %s)",
                (tick, snapshot_type, json.dumps(state)),
            )
            conn.commit()

    def get_latest_snapshot(self, snapshot_type: str = "full") -> Optional[dict]:
        conn = self._get_conn()
        with self._lock, conn.cursor() as cur:
            cur.execute(
                "SELECT tick, state FROM pangeia_snapshots "
                "WHERE snapshot_type = %s ORDER BY tick DESC LIMIT 1",
                (snapshot_type,),
            )
            row = cur.fetchone()
            if row:
                return {"tick": row[0], "state": row[1]}
            return None

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
