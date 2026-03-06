from fastapi import APIRouter
from ..schemas import (
    ScrapeCategoryRequest,
    ScrapeCategoryResponse,
    ScrapeProductResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeUrlRequest,
)
from ..services import scraper_service

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])


@router.post("/url", response_model=ScrapeProductResponse)
def scrape_url(request: ScrapeUrlRequest) -> ScrapeProductResponse:
    return scraper_service.scrape_url(request)


@router.post("/category", response_model=ScrapeCategoryResponse)
def scrape_category(request: ScrapeCategoryRequest) -> ScrapeCategoryResponse:
    return scraper_service.scrape_category(request)


@router.post("", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> ScrapeResponse:
    # Backward-compatible endpoint.
    return scraper_service.scrape(request)
