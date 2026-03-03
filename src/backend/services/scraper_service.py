import logging
from fastapi import HTTPException
from pydantic import ValidationError
from ..schemas import (
    ScrapeCategoryItem,
    ScrapeCategoryResponse,
    ScrapeProductResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from ..scrapers.url_product_scraper import scrape_product_data
from ..scrapers.category_product_scraper import CategoryScraper
from datetime import datetime, timezone
from ..logging_utils import configure_logging, format_exception_detail, log_event

logger = configure_logging()


def scrape(request: ScrapeRequest) -> ScrapeResponse:
    log_event(
        logger,
        logging.INFO,
        "scrape.request.received",
        url=request.url,
        category=request.category,
    )

    # Case 1: URL scraping
    if request.url and not request.category:
        result = scrape_product_data(request.url)
        current_time = datetime.now(timezone.utc) 

        if not result:
            log_event(
                logger,
                logging.WARNING,
                "scrape.request.url_failed",
                url=request.url,
                failure_reason="No result from scraper strategies",
            )
            raise HTTPException(status_code=400, detail="Failed to scrape product")

        log_event(
            logger,
            logging.INFO,
            "scrape.request.url_success",
            url=request.url,
            scraped_name=result.get("name"),
            has_price=isinstance(result.get("price"), (int, float)),
        )
        return ScrapeProductResponse(
            id=1,
            name=result["name"],
            url=result.get("url", request.url),
            category=None,
            created_at=current_time,
            price=result.get("price"),
        )

    # Case 2: Category scraping
    if request.category and not request.url:
        scraper = CategoryScraper()
        try:
            results = scraper.scrape(request.category, request.name)
        except Exception as exc:
            log_event(
                logger,
                logging.WARNING,
                "scrape.request.category_failed",
                category=request.category,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            raise HTTPException(status_code=400, detail="Failed to scrape category") from exc

        try:
            items = [ScrapeCategoryItem.model_validate(item) for item in results]
        except ValidationError as exc:
            log_event(
                logger,
                logging.ERROR,
                "scrape.request.category_validation_failed",
                category=request.category,
                error_count=len(exc.errors()),
                errors=exc.errors(),
            )
            raise HTTPException(
                status_code=500,
                detail="Scraper returned invalid category data",
            ) from exc

        log_event(
            logger,
            logging.INFO,
            "scrape.request.category_success",
            category=request.category,
            count=len(items),
        )

        return ScrapeCategoryResponse(
            category=request.category,
            count=len(items),
            data=items,
        )

    # Invalid input
    log_event(
        logger,
        logging.WARNING,
        "scrape.request.invalid_input",
        url=request.url,
        category=request.category,
        expected="Provide either url OR category",
    )
    raise HTTPException(
        status_code=400,
        detail="Provide either url OR category"
    )
