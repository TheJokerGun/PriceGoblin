from fastapi import APIRouter
from ..schemas import ScrapeRequest
from ..services import scraper_service

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])


@router.post("/")
def scrape(request: ScrapeRequest):
    return scraper_service.scrape(request)
