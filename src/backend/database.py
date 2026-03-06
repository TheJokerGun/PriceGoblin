from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from typing import Generator
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = PROJECT_ROOT / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "pricegoblin.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes", "on"}

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=SQL_ECHO
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db() -> None:
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_tracking_drop_url()
    _backfill_tracking_from_products()
    _migrate_products_drop_user_id()


def _migrate_tracking_drop_url() -> None:
    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='tracking'")
        ).first()
        if not table_exists:
            return

        columns = conn.execute(text("PRAGMA table_info(tracking)")).mappings().all()
        has_url_column = any(col.get("name") == "url" for col in columns)
        if not has_url_column:
            return

        try:
            conn.execute(text("ALTER TABLE tracking DROP COLUMN url"))
        except Exception:
            # Fallback for older SQLite versions without DROP COLUMN support.
            conn.execute(
                text(
                    """
                    CREATE TABLE tracking_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        user_id INTEGER,
                        product_id INTEGER,
                        is_active BOOLEAN,
                        created_at DATETIME,
                        FOREIGN KEY(user_id) REFERENCES users (id),
                        FOREIGN KEY(product_id) REFERENCES products (id)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO tracking_new (id, user_id, product_id, is_active, created_at)
                    SELECT id, user_id, product_id, is_active, created_at
                    FROM tracking
                    """
                )
            )
            conn.execute(text("DROP TABLE tracking"))
            conn.execute(text("ALTER TABLE tracking_new RENAME TO tracking"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tracking_id ON tracking (id)"))


def _backfill_tracking_from_products() -> None:
    with engine.begin() as conn:
        products_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        ).first()
        tracking_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='tracking'")
        ).first()
        if not products_exists or not tracking_exists:
            return

        products_columns = conn.execute(text("PRAGMA table_info(products)")).mappings().all()
        has_products_user_id = any(col.get("name") == "user_id" for col in products_columns)
        if not has_products_user_id:
            return

        conn.execute(
            text(
                """
                INSERT INTO tracking (user_id, product_id, is_active, created_at)
                SELECT p.user_id, p.id, 1, p.created_at
                FROM products p
                LEFT JOIN tracking t
                    ON t.product_id = p.id
                    AND t.user_id = p.user_id
                WHERE t.id IS NULL
                """
            )
        )


def _migrate_products_drop_user_id() -> None:
    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        ).first()
        if not table_exists:
            return

        columns = conn.execute(text("PRAGMA table_info(products)")).mappings().all()
        has_user_id_column = any(col.get("name") == "user_id" for col in columns)
        if not has_user_id_column:
            return

        # Rebuild table for SQLite compatibility and to remove legacy ownership column.
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(
            text(
                """
                CREATE TABLE products_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR,
                    url VARCHAR,
                    category VARCHAR,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO products_new (id, name, url, category, created_at)
                SELECT id, name, url, category, created_at
                FROM products
                """
            )
        )
        conn.execute(text("DROP TABLE products"))
        conn.execute(text("ALTER TABLE products_new RENAME TO products"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_id ON products (id)"))
        conn.execute(text("PRAGMA foreign_keys=ON"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


init_db()
