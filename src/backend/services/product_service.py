from typing import List

from sqlalchemy.orm import Session
from models import PriceEntry, Product
from datetime import datetime, timezone

def create_product(db: Session, user_id: int, data) -> Product:
    product = Product(
        name=data.name,
        url=data.url,
        category=data.category,
        user_id=user_id,
        created_at=datetime.now(timezone.utc)
    )
    #TODO: add product id, getting it from db prolly, depends on how we build the db
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_user_products(db: Session, user_id: int) -> List[Product]:
    return db.query(Product).filter(Product.user_id == user_id).all()
    #TODO: Check what all means


def get_product_by_id(db: Session, user_id: int, product_id: int) -> Product:
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


def delete_product(db: Session, product) -> None:
    db.delete(product)
    db.commit()

def get_product_prices(db: Session, product_id: int) -> List[PriceEntry]:
    return db.query(PriceEntry).filter(
        PriceEntry.product_id == product_id
    ).all()

def check_product_price(db: Session, product) -> PriceEntry:

    product = get_product_by_id(db, product.user_id, product.id)


    # TODO: Replace with real scraping logic
    fake_price = round(random.uniform(10, 500), 2)

    #TODO: Pull the infos of the productID 

    entry = PriceEntry(
        product_id=product.id,
        price=fake_price
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry