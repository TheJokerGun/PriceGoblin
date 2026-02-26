from typing import List

from sqlalchemy.orm import Session
from ..models import PriceEntry, Product
from datetime import datetime, timezone
import random
from ..scrapers.url_product_scraper import scrape_product_data

def create_product(db: Session, user_id: int, data) -> Product:
    product = Product(
        name=data.name,
        url=data.url,
        category=data.category,
        user_id=user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_user_products(db: Session, user_id: int) -> List[Product]:
    return db.query(Product).filter(Product.user_id == user_id).all()


def get_product_by_id(db: Session, user_id: int, product_id: int) -> Product | None:
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


def delete_product(db: Session, user_id: int, product_id: int) -> bool:
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True

def get_product_prices(db: Session, user_id: int, product_id: int) -> List[PriceEntry] | None:
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    return db.query(PriceEntry).filter(
        PriceEntry.product_id == product_id
    ).all()

def check_product_price(db: Session, user_id: int, product_id: int) -> PriceEntry | None:
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    scraped_price: float | None = None
    if product.url:
        scraped_data = scrape_product_data(product.url)
        if scraped_data and isinstance(scraped_data.get("price"), (int, float)):
            scraped_price = float(scraped_data["price"])

    price = scraped_price if scraped_price is not None else round(random.uniform(10, 500), 2)

    entry = PriceEntry(
        product_id=product.id,
        price=price
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry
