import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.backend.models import Base


class DatabaseTestCase(unittest.TestCase):
    """Shared in-memory SQLite setup for backend service tests."""

    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        Base.metadata.create_all(bind=self.engine)
        self.db: Session = self.SessionLocal()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
