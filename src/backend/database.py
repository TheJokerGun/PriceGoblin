# database.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///pricegoblin.db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# -------------------
# MODELS
# -------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    products = relationship("Product", back_populates="owner")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="products")

    prices = relationship("PriceEntry", back_populates="product")


class PriceEntry(Base):
    __tablename__ = "price_entries"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    checked_at = Column(DateTime, default=datetime.now(timezone.utc))

    product = relationship("Product", back_populates="prices")


# -------------------
# INIT DB
# -------------------

def init_db():
    Base.metadata.create_all(bind=engine)
