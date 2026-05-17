import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .time import utc_now


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.Lock()

    def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """
                create table if not exists readings (
                    id integer primary key autoincrement,
                    slug text not null,
                    plant text not null,
                    plant_id text not null,
                    timestamp text not null,
                    temperature real,
                    moisture real,
                    conductivity real,
                    light real,
                    battery real,
                    payload text not null
                )
                """
            )
            db.execute(
                """
                create table if not exists plant_cache (
                    plant_id text primary key,
                    fetched_at text not null,
                    payload text not null
                )
                """
            )

    def save_reading(self, slug: str, data: dict[str, Any]) -> None:
        with self.lock, sqlite3.connect(self.db_path) as db:
            db.execute(
                """
                insert into readings (
                    slug, plant, plant_id, timestamp, temperature, moisture,
                    conductivity, light, battery, payload
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slug,
                    data.get("plant", slug),
                    data.get("plant_id", ""),
                    data.get("timestamp", utc_now().isoformat()),
                    data.get("temperature"),
                    data.get("moisture"),
                    data.get("conductivity"),
                    data.get("light"),
                    data.get("battery"),
                    json.dumps(data),
                ),
            )

    def latest_reading(self, slug: str) -> dict[str, Any] | None:
        with self.lock, sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "select payload from readings where slug = ? order by timestamp desc limit 1",
                (slug,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def readings_since(self, slug: str, since: datetime) -> list[tuple]:
        with self.lock, sqlite3.connect(self.db_path) as db:
            return db.execute(
                """
                select timestamp, temperature, moisture, conductivity, light, battery
                from readings
                where slug = ? and timestamp >= ?
                order by timestamp
                """,
                (slug, since.isoformat()),
            ).fetchall()

    def get_cached_plant(self, plant_id: str) -> tuple[str, dict[str, Any]] | None:
        with self.lock, sqlite3.connect(self.db_path) as db:
            row = db.execute("select fetched_at, payload from plant_cache where plant_id = ?", (plant_id,)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def set_cached_plant(self, plant_id: str, payload: dict[str, Any]) -> None:
        with self.lock, sqlite3.connect(self.db_path) as db:
            db.execute(
                "insert or replace into plant_cache (plant_id, fetched_at, payload) values (?, ?, ?)",
                (plant_id, utc_now().isoformat(), json.dumps(payload)),
            )
