from sqlalchemy.orm import Session
from models import Product


def create_product(db: Session, user_id: int, data):
    product = Product(
        name=data.name,
        url=data.url,
        category=data.category,
        user_id=user_id
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_user_products(db: Session, user_id: int):
    return db.query(Product).filter(Product.user_id == user_id).all()


def get_product_by_id(db: Session, product_id: int, user_id: int):
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


def delete_product(db: Session, product):
    db.delete(product)
    db.commit()
