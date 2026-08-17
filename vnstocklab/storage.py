"""SQLite persistence for local VNStockLab user data."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from vnstocklab.analysis.alerts import AlertEvent, AlertRule, AlertSnapshot
from vnstocklab.analysis.portfolio import PortfolioTransaction


@dataclass(frozen=True)
class SQLiteRepository:
    """Small repository boundary that can later be replaced by a remote database."""

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS portfolio_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    shares INTEGER NOT NULL,
                    price REAL NOT NULL,
                    fee REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alert_rules (
                    symbol TEXT PRIMARY KEY,
                    stop_loss REAL,
                    target_price REAL,
                    minimum_score INTEGER
                );
                CREATE TABLE IF NOT EXISTS alert_events (
                    event_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    price REAL,
                    score INTEGER
                );
                CREATE TABLE IF NOT EXISTS alert_snapshots (
                    symbol TEXT PRIMARY KEY,
                    signal TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    score INTEGER
                );
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )
            rule_columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(alert_rules)").fetchall()
            }
            if "minimum_score" not in rule_columns:
                connection.execute("ALTER TABLE alert_rules ADD COLUMN minimum_score INTEGER")
            snapshot_columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(alert_snapshots)").fetchall()
            }
            if "score" not in snapshot_columns:
                connection.execute("ALTER TABLE alert_snapshots ADD COLUMN score INTEGER")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def list_portfolio_transactions(self) -> list[PortfolioTransaction]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT trade_date, symbol, action, shares, price, fee "
                "FROM portfolio_transactions ORDER BY trade_date, id"
            ).fetchall()
        return [
            PortfolioTransaction(
                pd.Timestamp(row["trade_date"]),
                str(row["symbol"]),
                str(row["action"]),
                int(row["shares"]),
                float(row["price"]),
                float(row["fee"]),
            )
            for row in rows
        ]

    def add_portfolio_transaction(self, transaction: PortfolioTransaction) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO portfolio_transactions "
                "(trade_date, symbol, action, shares, price, fee) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    transaction.date.isoformat(),
                    transaction.symbol,
                    transaction.action,
                    transaction.shares,
                    transaction.price,
                    transaction.fee,
                ),
            )

    def delete_last_portfolio_transaction(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM portfolio_transactions WHERE id = "
                "(SELECT id FROM portfolio_transactions ORDER BY id DESC LIMIT 1)"
            )

    def clear_portfolio_transactions(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM portfolio_transactions")

    def list_alert_rules(self) -> list[AlertRule]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT symbol, stop_loss, target_price, minimum_score "
                "FROM alert_rules ORDER BY symbol"
            ).fetchall()
        return [
            AlertRule(
                str(row["symbol"]),
                float(row["stop_loss"]) if row["stop_loss"] is not None else None,
                float(row["target_price"]) if row["target_price"] is not None else None,
                int(row["minimum_score"]) if row["minimum_score"] is not None else None,
            )
            for row in rows
        ]

    def upsert_alert_rule(self, rule: AlertRule) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO alert_rules (symbol, stop_loss, target_price, minimum_score) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(symbol) DO UPDATE SET "
                "stop_loss=excluded.stop_loss, target_price=excluded.target_price, "
                "minimum_score=excluded.minimum_score",
                (rule.symbol, rule.stop_loss, rule.target_price, rule.minimum_score),
            )

    def delete_alert_rule(self, symbol: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM alert_rules WHERE symbol = ?", (symbol,))
            connection.execute("DELETE FROM alert_snapshots WHERE symbol = ?", (symbol,))

    def list_alert_events(self) -> list[AlertEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM alert_events ORDER BY occurred_at DESC"
            ).fetchall()
        return [
            AlertEvent(
                str(row["event_id"]),
                pd.Timestamp(row["occurred_at"]),
                str(row["symbol"]),
                str(row["category"]),
                str(row["severity"]),
                str(row["message"]),
                float(row["price"]) if row["price"] is not None else None,
                int(row["score"]) if row["score"] is not None else None,
            )
            for row in rows
        ]

    def add_alert_events(self, events: Iterator[AlertEvent]) -> None:
        values = [
            (
                event.event_id,
                event.occurred_at.isoformat(),
                event.symbol,
                event.category,
                event.severity,
                event.message,
                event.price,
                event.score,
            )
            for event in events
        ]
        if not values:
            return
        with self._connect() as connection:
            connection.executemany(
                "INSERT OR IGNORE INTO alert_events "
                "(event_id, occurred_at, symbol, category, severity, message, price, score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )

    def clear_alert_events(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM alert_events")

    def list_alert_snapshots(self) -> dict[str, AlertSnapshot]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT symbol, signal, trend, score FROM alert_snapshots"
            ).fetchall()
        return {
            str(row["symbol"]): AlertSnapshot(
                str(row["signal"]),
                str(row["trend"]),
                score=int(row["score"]) if row["score"] is not None else None,
            )
            for row in rows
        }

    def upsert_alert_snapshots(self, snapshots: dict[str, AlertSnapshot]) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT INTO alert_snapshots (symbol, signal, trend, score) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(symbol) DO UPDATE SET signal=excluded.signal, "
                "trend=excluded.trend, score=excluded.score",
                [
                    (symbol, snapshot.signal, snapshot.trend, snapshot.score)
                    for symbol, snapshot in snapshots.items()
                ],
            )

    def get_metadata(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_metadata WHERE key = ?", (key,)
            ).fetchone()
        return str(row["value"]) if row is not None and row["value"] is not None else None

    def set_metadata(self, key: str, value: Any) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO app_metadata (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )
