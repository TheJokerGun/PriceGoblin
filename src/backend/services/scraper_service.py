from fastapi import HTTPException
from ..schemas import ScrapeRequest
from ..scrapers.url_product_scraper import scrape_product_data
from ..scrapers.category_product_scraper import CategoryScraper
from datetime import datetime, timezone


def scrape(request: ScrapeRequest):

    # Case 1: URL scraping
    if request.url and not request.category:
        result = scrape_product_data(request.url)
        current_time = datetime.now(timezone.utc) 

        if not result:
            raise HTTPException(status_code=400, detail="Failed to scrape product")

        return {
            "id": 1,
            "name": result["name"],
            "url": result.get("url", request.url),
            "category": None,
            "created_at": current_time,
            "price": result.get("price")
        }

    # Case 2: Category scraping
    if request.category and not request.url:
        scraper = CategoryScraper()
        results = scraper.scrape(request.category)

        return {
            "type": "category",
            "count": len(results),
            "data": results
        }

    # Invalid input
    raise HTTPException(
        status_code=400,
        detail="Provide either url OR category"
    )
