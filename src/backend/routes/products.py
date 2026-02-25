from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PriceResponse, ProductCreate, ProductResponse
from ..services import auth_service, product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user)
):
    if not product.name and not product.url and not product.category:
        raise HTTPException(
            status_code=400,
            detail="At least one of name, url, or category must be provided"
        )
    return product_service.create_product(db, current_user.id, product)


@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user)
):
    return product_service.get_user_products(db, current_user.id)

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user)
):
    success = product_service.delete_product(db, current_user.id, product_id)
    #TODO: Figure out if there is a connection table with tracked products and users or just a tracked items table
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product deleted successfully"}

@router.get("/{product_id}/prices", response_model=list[PriceResponse])
def get_product_prices(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user)
):
    prices = product_service.get_product_prices(db, current_user.id, product_id)
    if prices is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return [
        PriceResponse(
            id=entry.id,
            price=entry.price,
            checked_at=entry.created_at
        )
        for entry in prices
    ]

@router.post("/{product_id}/check-price", response_model=PriceResponse)
def check_product_price(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user)
):
    result = product_service.check_product_price(db, current_user.id, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return PriceResponse(
        id=result.id,
        price=result.price,
        checked_at=result.created_at
    )
