# bot/db.py
import aiosqlite
from typing import Optional, List, Tuple
from config import DATABASE_URL

def _extract_sqlite_path(db_url: str) -> str:
    # "sqlite:///db.sqlite" -> "db.sqlite"
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return db_url

DB_PATH = _extract_sqlite_path(DATABASE_URL)

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    telegram_user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(owner_user_id, name),
    FOREIGN KEY(owner_user_id) REFERENCES users(telegram_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    contact_value TEXT NOT NULL,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()

async def ensure_user(telegram_user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_user_id) VALUES (?)",
            (telegram_user_id,)
        )
        await db.commit()

# ---------- Категории ----------

async def add_category(telegram_user_id: int, category_name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO categories (owner_user_id, name) VALUES (?, ?)",
                (telegram_user_id, category_name)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def list_categories(user_id: int) -> List[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name FROM categories WHERE owner_user_id = ? ORDER BY name ASC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

async def list_categories_full(user_id: int) -> List[Tuple[int, str]]:
    """
    Возвращает список (id, name) для построения клавиатуры.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name FROM categories WHERE owner_user_id = ? ORDER BY name ASC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [(r[0], r[1]) for r in rows]

async def get_category_id(user_id: int, category_name: str) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id FROM categories
            WHERE owner_user_id = ? AND name = ?
            """,
            (user_id, category_name)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_category_name_by_id(user_id: int, category_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT name FROM categories
            WHERE owner_user_id = ? AND id = ?
            """,
            (user_id, category_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def delete_category(user_id: int, category_id: int) -> bool:
    """
    Удаляет категорию пользователя (и каскадно все её контакты).
    Возвращает True если реально что-то удалилось.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            DELETE FROM categories
            WHERE owner_user_id = ? AND id = ?
            """,
            (user_id, category_id)
        )
        await db.commit()
        return cursor.rowcount > 0

# ---------- Контакты ----------

async def add_contact_in_category(
    category_id: int,
    display_name: str,
    contact_value: str
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO contacts (category_id, display_name, contact_value)
            VALUES (?, ?, ?)
            """,
            (category_id, display_name, contact_value)
        )
        await db.commit()

async def list_contacts_in_category(
    category_id: int
) -> List[Tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT display_name, contact_value
            FROM contacts
            WHERE category_id = ?
            ORDER BY display_name ASC
            """,
            (category_id,)
        )
        rows = await cursor.fetchall()
        return [(r[0], r[1]) for r in rows]

async def remove_contact_in_category(
    category_id: int,
    display_name: str
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            DELETE FROM contacts
            WHERE category_id = ? AND display_name = ?
            """,
            (category_id, display_name)
        )
        await db.commit()
        return cursor.rowcount > 0
