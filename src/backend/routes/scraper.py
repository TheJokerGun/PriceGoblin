from fastapi import APIRouter
from ..schemas import ScrapeRequest, ScrapeResponse
from ..services import scraper_service

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])


@router.post("", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> ScrapeResponse:
    return scraper_service.scrape(request)
