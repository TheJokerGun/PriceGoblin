from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import (
    ScrapeCategoryRequest,
    ScrapeCategoryResponse,
    ScrapeProductResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeUrlRequest,
)
from ..services import auth_service, product_service, scraper_service

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])


@router.post("/url", response_model=ScrapeProductResponse)
def scrape_url(
    request: ScrapeUrlRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user),
) -> ScrapeProductResponse:
    product = product_service.create_product_from_scraped_url(
        db,
        current_user.id,
        request.url,
        target_price=request.target_price,
        locale=getattr(current_user, "locale", None),
    )
    latest_price = product_service.get_latest_product_price(db, product.id)
    return ScrapeProductResponse(
        id=product.id,
        name=product.name or "Unknown",
        url=product.url or request.url,
        category=product.category,
        created_at=product.created_at,
        price=latest_price.price if latest_price else None,
        image_url=product.image_url,
    )


@router.post("/category", response_model=ScrapeCategoryResponse)
def scrape_category(
    request: ScrapeCategoryRequest,
    current_user=Depends(auth_service.get_current_user),
) -> ScrapeCategoryResponse:
    return scraper_service.scrape_category(request, locale=getattr(current_user, "locale", None))


@router.post("", response_model=ScrapeResponse)
def scrape(
    request: ScrapeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user),
) -> ScrapeResponse:
    # Backward-compatible endpoint.
    if request.url and not request.category:
        return scrape_url(
            ScrapeUrlRequest(url=request.url, target_price=request.target_price),
            db,
            current_user,
        )
    if request.category and not request.url:
        return scraper_service.scrape_category(
            ScrapeCategoryRequest(category=request.category, name=request.name, limit=10),
            locale=getattr(current_user, "locale", None),
        )
    return scraper_service.scrape(request, locale=getattr(current_user, "locale", None))
