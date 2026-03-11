import logging
from fastapi import HTTPException
from pydantic import ValidationError
from ..schemas import (
    ScrapeCategoryRequest,
    ScrapeCategoryItem,
    ScrapeCategoryResponse,
    ScrapeProductResponse,
    ScrapeRequest,
    ScrapeUrlRequest,
    ScrapeResponse,
)
from ..scrapers.url_product_scraper import (
    get_site_key,
    get_unsupported_url_sites,
    is_url_site_explicitly_unsupported,
    scrape_product_data,
)
from ..scrapers.category_product_scraper import CategoryScraper
from datetime import datetime, timezone
from ..logging_utils import configure_logging, format_exception_detail, log_event

logger = configure_logging()


def scrape_url(request: ScrapeUrlRequest) -> ScrapeProductResponse:
    site_key = get_site_key(request.url)
    log_event(
        logger,
        logging.INFO,
        "scrape.request.received",
        url=request.url,
        category=None,
    )

    if is_url_site_explicitly_unsupported(request.url):
        log_event(
            logger,
            logging.WARNING,
            "scrape.request.url_unsupported_site",
            url=request.url,
            site_key=site_key,
            unsupported_sites=get_unsupported_url_sites(),
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNSUPPORTED_SITE",
                "site": site_key,
                "unsupported_sites": get_unsupported_url_sites(),
                "message": "URL domain is currently unsupported for scraping",
            },
        )

    result = scrape_product_data(request.url)
    current_time = datetime.now(timezone.utc)

    if not result:
        log_event(
            logger,
            logging.WARNING,
            "scrape.request.url_failed",
            url=request.url,
            site_key=site_key,
            failure_reason="No result from scraper strategies",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "SCRAPE_FAILED",
                "site": site_key,
                "message": "Failed to scrape product",
            },
        )

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
        image_url=result.get("image_url"),
    )


def scrape_category(request: ScrapeCategoryRequest) -> ScrapeCategoryResponse:
    category = request.category.strip().lower()
    limit = max(1, min(request.limit, 50))

    log_event(
        logger,
        logging.INFO,
        "scrape.request.received",
        url=None,
        category=category,
    )

    scraper = CategoryScraper()
    try:
        results = scraper.scrape(category, request.name)
    except Exception as exc:
        log_event(
            logger,
            logging.WARNING,
            "scrape.request.category_failed",
            category=category,
            error_type=type(exc).__name__,
            detail=format_exception_detail(exc),
        )
        raise HTTPException(status_code=400, detail="Failed to scrape category") from exc

    # Keep candidate payload compact for frontend selection workflows.
    results = results[:limit]

    try:
        items = [ScrapeCategoryItem.model_validate(item) for item in results]
    except ValidationError as exc:
        log_event(
            logger,
            logging.ERROR,
            "scrape.request.category_validation_failed",
            category=category,
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
        category=category,
        count=len(items),
        limit=limit,
    )

    return ScrapeCategoryResponse(
        category=category,
        count=len(items),
        data=items,
    )


def scrape(request: ScrapeRequest) -> ScrapeResponse:
    # Legacy combined endpoint compatibility.
    if request.url and not request.category:
        return scrape_url(ScrapeUrlRequest(url=request.url))

    if request.category and not request.url:
        return scrape_category(
            ScrapeCategoryRequest(category=request.category, name=request.name, limit=10)
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
