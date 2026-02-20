import random
from sqlalchemy.orm import Session
from models import PriceEntry


def check_price(db: Session, product):
    # TODO: Replace with real scraping logic
    fake_price = round(random.uniform(10, 500), 2)

    entry = PriceEntry(
        product_id=product.id,
        price=fake_price
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry


def get_price_history(db: Session, product_id: int):
    return db.query(PriceEntry).filter(
        PriceEntry.product_id == product_id
    ).all()
