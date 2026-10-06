"""Persistência local em SQLite do perfil, catálogo, preços e fontes."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class LocalStore:
    def __init__(self):
        self.database_path = Path.home() / ".radar_streaming.sqlite3"
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS watched (title_id TEXT PRIMARY KEY, watched_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS reviews (
                title_id TEXT PRIMARY KEY, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                review_text TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS titles (
                title_id TEXT PRIMARY KEY, external_id TEXT, title TEXT NOT NULL,
                kind TEXT NOT NULL, year INTEGER, genres TEXT NOT NULL,
                synopsis TEXT NOT NULL, providers TEXT NOT NULL, poster TEXT NOT NULL,
                release_date TEXT, source TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS prices (
                service TEXT PRIMARY KEY, monthly_price REAL NOT NULL,
                source_url TEXT NOT NULL, checked_at TEXT, status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS custom_services (
                name TEXT PRIMARY KEY COLLATE NOCASE,
                monthly_price REAL NOT NULL CHECK(monthly_price > 0),
                genres TEXT NOT NULL,
                source_url TEXT NOT NULL DEFAULT '',
                entered_price REAL,
                entered_currency TEXT NOT NULL DEFAULT 'BRL',
                conversion_rate REAL,
                conversion_date TEXT NOT NULL DEFAULT ''
            )"""
        )
        custom_columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(custom_services)")
        }
        for column, definition in (
            ("entered_price", "REAL"),
            ("entered_currency", "TEXT NOT NULL DEFAULT 'BRL'"),
            ("conversion_rate", "REAL"),
            ("conversion_date", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in custom_columns:
                self.connection.execute(f"ALTER TABLE custom_services ADD COLUMN {column} {definition}")
        self.connection.execute(
            "UPDATE custom_services SET entered_price = monthly_price WHERE entered_price IS NULL"
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS source_status (
                source TEXT PRIMARY KEY, checked_at TEXT NOT NULL,
                status TEXT NOT NULL, detail TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    @staticmethod
    def _now():
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def seed(self, titles, services, price_sources):
        """Atualiza o catálogo inicial sem substituir registros importados de fontes online."""
        now = self._now()
        seed_ids = [item["id"] for item in titles]
        try:
            self.connection.execute("BEGIN")
            for item in titles:
                self.connection.execute(
                    """INSERT INTO titles
                       (title_id, external_id, title, kind, year, genres, synopsis,
                        providers, poster, release_date, source, updated_at)
                       VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, 'seed', ?)
                       ON CONFLICT(title_id) DO UPDATE SET
                         title=excluded.title, kind=excluded.kind, year=excluded.year,
                         genres=excluded.genres, synopsis=excluded.synopsis,
                         providers=excluded.providers, poster=excluded.poster,
                         release_date=excluded.release_date, updated_at=excluded.updated_at
                       WHERE titles.source='seed'""",
                    (
                        item["id"], item["title"], item["kind"], item["year"],
                        json.dumps(item["genres"], ensure_ascii=False), item["synopsis"],
                        json.dumps(item["providers"], ensure_ascii=False), item["poster"],
                        f"{item['year']}-01-01", now,
                    ),
                )
            if seed_ids:
                placeholders = ",".join("?" for _ in seed_ids)
                self.connection.execute(
                    f"DELETE FROM titles WHERE source='seed' AND title_id NOT IN ({placeholders})",
                    seed_ids,
                )
            self.connection.execute(
                "DELETE FROM watched WHERE title_id NOT IN (SELECT title_id FROM titles)"
            )
            self.connection.execute(
                "DELETE FROM reviews WHERE title_id NOT IN (SELECT title_id FROM titles)"
            )
            for service in services:
                self.connection.execute(
                    """INSERT OR IGNORE INTO prices
                       (service, monthly_price, source_url, checked_at, status, updated_at)
                       VALUES (?, ?, ?, NULL, 'aguardando verificação', ?)""",
                    (service["name"], service["monthly_price"], price_sources[service["name"]], now),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def get_titles(self):
        rows = self.connection.execute(
            """SELECT title_id, title, kind, year, genres, synopsis, providers, poster,
                      release_date, source FROM titles
               ORDER BY COALESCE(release_date, '0000-00-00') DESC, title"""
        ).fetchall()
        titles = []
        for row in rows:
            titles.append({
                "id": row[0], "title": row[1], "kind": row[2], "year": row[3] or 0,
                "genres": json.loads(row[4]), "synopsis": row[5],
                "providers": json.loads(row[6]), "poster": row[7],
                "release_date": row[8], "source": row[9],
            })
        return titles

    def replace_catalog_snapshot(self, source, releases):
        """Substitui o snapshot de catálogo só após uma consulta completa."""
        if source not in {"tmdb", "justwatch"}:
            raise ValueError("Fonte de catálogo não reconhecida")
        merged = {}
        for item, service in releases:
            record = merged.setdefault(item["id"], {**item, "providers": set()})
            record["providers"].add(service)

        now = self._now()
        try:
            self.connection.execute("BEGIN")
            self.connection.execute("DELETE FROM titles WHERE source IN ('tmdb', 'justwatch') AND title_id NOT IN (SELECT title_id FROM watched)")
            for item in merged.values():
                self.connection.execute(
                    """INSERT INTO titles
                       (title_id, external_id, title, kind, year, genres, synopsis,
                        providers, poster, release_date, source, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(title_id) DO UPDATE SET
                         external_id=excluded.external_id, title=excluded.title,
                         kind=excluded.kind, year=excluded.year, genres=excluded.genres,
                         synopsis=excluded.synopsis, providers=excluded.providers,
                         poster=excluded.poster, release_date=excluded.release_date,
                         source=excluded.source, updated_at=excluded.updated_at""",
                    (
                        item["id"], str(item.get("tmdb_id", item.get("external_id", ""))),
                        item["title"], item["kind"], item["year"],
                        json.dumps(item["genres"], ensure_ascii=False), item["synopsis"],
                        json.dumps(sorted(item["providers"]), ensure_ascii=False),
                        item["poster"], item["release_date"], source, now,
                    ),
                )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def get_genres(self, defaults):
        row = self.connection.execute(
            "SELECT value FROM preferences WHERE key = 'favorite_genres'"
        ).fetchone()
        return json.loads(row[0]) if row else list(defaults)

    def save_genres(self, genres):
        self.connection.execute(
            "INSERT INTO preferences(key, value) VALUES('favorite_genres', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (json.dumps(genres, ensure_ascii=False),),
        )
        self.connection.commit()

    def get_setting(self, key, default=None):
        row = self.connection.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            return row[0]

    def save_setting(self, key, value):
        self.connection.execute(
            "INSERT INTO preferences(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self.connection.commit()

    def get_tmdb_token(self):
        row = self.connection.execute(
            "SELECT value FROM preferences WHERE key = 'tmdb_read_token'"
        ).fetchone()
        return row[0] if row else ""

    def save_tmdb_token(self, token):
        self.connection.execute(
            "INSERT INTO preferences(key, value) VALUES('tmdb_read_token', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (token.strip(),),
        )
        self.connection.commit()

    def get_watched_ids(self):
        return {row[0] for row in self.connection.execute("SELECT title_id FROM watched")}

    def mark_watched(self, title_id):
        self.connection.execute("INSERT OR IGNORE INTO watched(title_id) VALUES(?)", (title_id,))
        self.connection.commit()

    def get_reviews(self):
        rows = self.connection.execute(
            "SELECT title_id, rating, review_text, updated_at FROM reviews"
        ).fetchall()
        return {
            row[0]: {"rating": row[1], "text": row[2], "updated_at": row[3]}
            for row in rows
        }

    def save_review(self, title_id, rating, review_text):
        if not 1 <= int(rating) <= 5:
            raise ValueError("A avaliação deve ter de 1 a 5 estrelas")
        now = self._now()
        try:
            self.connection.execute("BEGIN")
            self.connection.execute("INSERT OR IGNORE INTO watched(title_id) VALUES(?)", (title_id,))
            self.connection.execute(
                """INSERT INTO reviews(title_id, rating, review_text, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(title_id) DO UPDATE SET
                     rating=excluded.rating, review_text=excluded.review_text,
                     updated_at=excluded.updated_at""",
                (title_id, int(rating), review_text.strip(), now),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def remove_review(self, title_id):
        self.connection.execute("DELETE FROM reviews WHERE title_id = ?", (title_id,))
        self.connection.commit()

    def remove_watched(self, title_id):
        self.connection.execute("DELETE FROM watched WHERE title_id = ?", (title_id,))
        self.connection.execute("DELETE FROM reviews WHERE title_id = ?", (title_id,))
        self.connection.commit()

    def add_custom_service(
        self, name, monthly_price_brl, genres, source_url="", entered_price=None,
        entered_currency="BRL", conversion_rate=None, conversion_date="",
    ):
        name = name.strip()
        price_brl = float(monthly_price_brl)
        entry_value = float(entered_price if entered_price is not None else price_brl)
        if not name or price_brl <= 0 or entry_value <= 0:
            raise ValueError("Nome e preço mensal positivo são obrigatórios")
        if entered_currency not in {"BRL", "USD"}:
            raise ValueError("Moeda não suportada")
        now = self._now()
        try:
            self.connection.execute("BEGIN")
            self.connection.execute(
                """INSERT INTO custom_services
                   (name, monthly_price, genres, source_url, entered_price, entered_currency,
                    conversion_rate, conversion_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name, price_brl, json.dumps(sorted(set(genres)), ensure_ascii=False),
                    source_url.strip(), entry_value, entered_currency, conversion_rate,
                    conversion_date,
                ),
            )
            self.connection.execute(
                "INSERT INTO prices(service, monthly_price, source_url, checked_at, status, updated_at) "
                "VALUES (?, ?, ?, NULL, 'informado manualmente', ?) "
                "ON CONFLICT(service) DO UPDATE SET monthly_price=excluded.monthly_price, "
                "source_url=excluded.source_url, status='informado manualmente', updated_at=excluded.updated_at",
                (name, price_brl, source_url.strip(), now),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def get_custom_services(self):
        rows = self.connection.execute(
            """SELECT name, monthly_price, genres, source_url, entered_price,
                      entered_currency, conversion_rate, conversion_date
               FROM custom_services ORDER BY name COLLATE NOCASE"""
        ).fetchall()
        return [
            {
                "name": row[0], "monthly_price": row[1], "genres": json.loads(row[2]),
                "source_url": row[3], "entered_price": row[4],
                "entered_currency": row[5], "conversion_rate": row[6], "conversion_date": row[7],
            }
            for row in rows
        ]

    def get_services(self, services):
        rows = self.connection.execute(
            "SELECT service, monthly_price, checked_at, status FROM prices"
        ).fetchall()
        stored = {row[0]: row[1:] for row in rows}
        all_services = list(services)
        known_names = {service["name"].casefold() for service in all_services}
        all_services.extend(
            service for service in self.get_custom_services()
            if service["name"].casefold() not in known_names
        )
        result = []
        for service in all_services:
            price, checked_at, status = stored.get(
                service["name"], (service["monthly_price"], None, "sem verificação")
            )
            result.append({**service, "monthly_price": price, "checked_at": checked_at, "price_status": status})
        return result

    def update_price(self, service, source_url, status, monthly_price=None):
        now = self._now()
        self.connection.execute(
            """UPDATE prices SET monthly_price = COALESCE(?, monthly_price),
               source_url = ?, checked_at = ?, status = ?,
               updated_at = CASE WHEN ? IS NULL THEN updated_at ELSE ? END
               WHERE service = ?""",
            (monthly_price, source_url, now, status, monthly_price, now, service),
        )
        self.connection.commit()

    def record_source_status(self, source, status, detail):
        self.connection.execute(
            """INSERT INTO source_status(source, checked_at, status, detail)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(source) DO UPDATE SET checked_at=excluded.checked_at,
                 status=excluded.status, detail=excluded.detail""",
            (source, self._now(), status, detail),
        )
        self.connection.commit()

    def get_source_status(self, source):
        return self.connection.execute(
            "SELECT checked_at, status, detail FROM source_status WHERE source = ?", (source,)
        ).fetchone()
