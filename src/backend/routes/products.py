from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import ProductCreate, ProductResponse
from services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # TODO: replace user_id with auth logic
    user_id = 1
    return product_service.create_product(db, user_id, product)


@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    user_id = 1
    return product_service.get_user_products(db, user_id)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    user_id = 1
    success = product_service.delete_product(db, user_id, product_id)
    #TODO: Figure out if there is a connection table with tracked products and users or just a tracked items table
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product deleted successfully"}

@router.get("/{product_id}/prices")
def get_product_prices(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product_prices(db, product_id)

@router.post("/{product_id}/check-price")
def check_product_price(product_id: int, db: Session = Depends(get_db)):
    result = product_service.check_product_price(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result
