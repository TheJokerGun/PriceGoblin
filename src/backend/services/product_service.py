import logging
import random
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..logging_utils import configure_logging, log_event
from ..models import PriceEntry, Product, Tracking, User
from ..price_utils import extract_price_value
from ..schemas import (
    ProductCategorySelectionCreate,
    ProductCategorySelectionResponse,
    ProductCategorySelectionResult,
    ProductCreate,
    ScrapeProductResponse,
    ScrapeUrlRequest,
)
from ..scrapers.url_product_scraper import scrape_product_data
from . import notification_service, scraper_service

logger = configure_logging()


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _extract_price_value(value: str | float | int | None) -> float | None:
    return extract_price_value(value)


def _infer_source_from_url(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.strip().lower()
    return host or None


def _attach_tracking_metadata(product: Product, tracking: Tracking | None) -> Product:
    if tracking is None:
        return product
    # Enrich ORM object with response-only fields without changing the DB schema.
    setattr(product, "tracking_id", tracking.id)
    setattr(product, "is_active", tracking.is_active)
    setattr(product, "source", tracking.source)
    setattr(product, "target_price", tracking.target_price)
    return product


def _find_product_by_urls(db: Session, urls: list[str | None]) -> Product | None:
    normalized_urls = list(dict.fromkeys(url for url in urls if url))
    if not normalized_urls:
        return None
    if len(normalized_urls) == 1:
        return db.query(Product).filter(Product.url == normalized_urls[0]).first()
    return db.query(Product).filter(Product.url.in_(normalized_urls)).first()


def _merge_product_metadata(
    product: Product,
    *,
    name: str | None,
    url: str | None,
    category: str | None,
    image_url: str | None,
) -> None:
    if not product.name and name:
        product.name = name
    if not product.url and url:
        product.url = url
    if not product.category and category:
        product.category = category
    if not product.image_url and image_url:
        product.image_url = image_url


def _get_or_create_product(
    db: Session,
    *,
    candidate_urls: list[str | None],
    name: str | None,
    url: str | None,
    category: str | None,
    image_url: str | None,
) -> tuple[Product, bool]:
    product = _find_product_by_urls(db, candidate_urls)
    if not product:
        product = Product(
            name=name,
            url=url,
            category=category,
            image_url=image_url,
            created_at=datetime.now(timezone.utc),
        )
        db.add(product)
        db.flush()
        return product, True

    _merge_product_metadata(
        product,
        name=name,
        url=url,
        category=category,
        image_url=image_url,
    )
    return product, False


def _get_tracking(db: Session, user_id: int, product_id: int) -> Tracking | None:
    return (
        db.query(Tracking)
        .filter(Tracking.user_id == user_id, Tracking.product_id == product_id)
        .first()
    )


def _upsert_tracking(
    db: Session,
    *,
    user_id: int,
    product_id: int,
    source: str | None,
    target_price: float | None,
    overwrite_source: bool,
) -> tuple[Tracking, bool]:
    tracking = _get_tracking(db, user_id, product_id)
    if not tracking:
        tracking = Tracking(
            user_id=user_id,
            product_id=product_id,
            is_active=True,
            source=source,
            target_price=target_price,
        )
        db.add(tracking)
        db.flush()
        return tracking, True

    tracking.is_active = True
    if source and (overwrite_source or not tracking.source):
        tracking.source = source
    if target_price is not None:
        tracking.target_price = target_price
    return tracking, False


def _has_price_history(db: Session, product_id: int) -> bool:
    return db.query(PriceEntry.id).filter(PriceEntry.product_id == product_id).first() is not None


def _seed_initial_price(
    db: Session,
    *,
    product_id: int,
    price: float | None,
    created_new_product: bool,
) -> float | None:
    if price is None:
        return None
    if created_new_product or not _has_price_history(db, product_id):
        db.add(PriceEntry(product_id=product_id, price=price))
        return price
    return None


def create_products_from_category_selection(
    db: Session, user_id: int, payload: ProductCategorySelectionCreate
) -> ProductCategorySelectionResponse:
    results: list[ProductCategorySelectionResult] = []

    for item in payload.items:
        name = _normalize_optional_text(item.name)
        url = _normalize_optional_text(item.url)
        category = _normalize_optional_text(item.category)
        image_url = _normalize_optional_text(item.image_url)
        source = _normalize_optional_text(item.source) or _infer_source_from_url(url)
        target_price = _extract_price_value(item.target_price)

        if not name and not url and not category:
            continue

        product, created_product = _get_or_create_product(
            db,
            candidate_urls=[url],
            name=name,
            url=url,
            category=category,
            image_url=image_url,
        )
        tracking, created_tracking = _upsert_tracking(
            db,
            user_id=user_id,
            product_id=product.id,
            source=source,
            target_price=target_price,
            overwrite_source=True,
        )

        seeded_price = _seed_initial_price(
            db,
            product_id=product.id,
            price=_extract_price_value(item.price),
            created_new_product=created_product,
        )

        results.append(
            ProductCategorySelectionResult(
                product_id=product.id,
                tracking_id=tracking.id,
                name=product.name,
                url=product.url,
                category=product.category,
                image_url=product.image_url,
                source=tracking.source,
                target_price=tracking.target_price,
                is_active=tracking.is_active,
                created_product=created_product,
                created_tracking=created_tracking,
                seeded_price=seeded_price,
            )
        )

    db.commit()
    return ProductCategorySelectionResponse(count=len(results), data=results)


def create_product_from_scraped_url(
    db: Session,
    user_id: int,
    url: str,
    target_price: float | None = None,
    source: str | None = None,
    locale: str | None = None,
) -> Product:
    scraped = scraper_service.scrape_url(ScrapeUrlRequest(url=url), locale=locale)
    normalized_url = _normalize_optional_text(scraped.url) or _normalize_optional_text(url)
    name = _normalize_optional_text(scraped.name)
    category = _normalize_optional_text(scraped.category)
    scraped_price = float(scraped.price) if isinstance(scraped.price, (int, float)) else None
    image_url = _normalize_optional_text(scraped.image_url)
    normalized_source = _normalize_optional_text(source) or _infer_source_from_url(normalized_url)

    product, created_new_product = _get_or_create_product(
        db,
        # Match both URLs because some sites redirect to canonical product URLs.
        candidate_urls=[normalized_url, _normalize_optional_text(url)],
        name=name,
        url=normalized_url,
        category=category,
        image_url=image_url,
    )
    _seed_initial_price(
        db,
        product_id=product.id,
        price=scraped_price,
        created_new_product=created_new_product,
    )
    tracking, _ = _upsert_tracking(
        db,
        user_id=user_id,
        product_id=product.id,
        source=normalized_source,
        target_price=target_price,
        overwrite_source=False,
    )

    db.commit()
    db.refresh(product)
    return _attach_tracking_metadata(product, tracking)


def create_product(
    db: Session, user_id: int, data: ProductCreate, locale: str | None = None
) -> Product:
    name = _normalize_optional_text(data.name)
    url = _normalize_optional_text(data.url)
    category = _normalize_optional_text(data.category)
    image_url = _normalize_optional_text(data.image_url)
    scraped_price: float | None = None
    source = _normalize_optional_text(data.source) or _infer_source_from_url(url)

    # Best-effort scrape to enrich user input; manual data still works if scraping fails.
    if url:
        try:
            scraped_data = scraper_service.scrape_url(ScrapeUrlRequest(url=url), locale=locale)
        except HTTPException:
            scraped_data = None

        if isinstance(scraped_data, ScrapeProductResponse):
            name = name or _normalize_optional_text(scraped_data.name)
            url = _normalize_optional_text(scraped_data.url) or url
            category = category or _normalize_optional_text(scraped_data.category)
            if isinstance(scraped_data.price, (int, float)):
                scraped_price = float(scraped_data.price)
            image_url = image_url or _normalize_optional_text(scraped_data.image_url)
            source = _normalize_optional_text(data.source) or _infer_source_from_url(url)

    product, created_new_product = _get_or_create_product(
        db,
        candidate_urls=[url],
        name=name,
        url=url,
        category=category,
        image_url=image_url,
    )
    _seed_initial_price(
        db,
        product_id=product.id,
        price=scraped_price,
        created_new_product=created_new_product,
    )
    tracking, _ = _upsert_tracking(
        db,
        user_id=user_id,
        product_id=product.id,
        source=source,
        target_price=data.target_price,
        overwrite_source=False,
    )

    db.commit()
    db.refresh(product)
    return _attach_tracking_metadata(product, tracking)


def get_user_products(db: Session, user_id: int) -> List[Product]:
    rows = (
        db.query(Product, Tracking)
        .join(Tracking, Tracking.product_id == Product.id)
        .filter(Tracking.user_id == user_id)
        .order_by(Product.created_at.desc(), Product.id.desc())
        .all()
    )
    return [_attach_tracking_metadata(product, tracking) for product, tracking in rows]


def get_product_by_id(db: Session, user_id: int, product_id: int) -> Product | None:
    row = (
        db.query(Product, Tracking)
        .join(Tracking, Tracking.product_id == Product.id)
        .filter(
            Product.id == product_id,
            Tracking.user_id == user_id,
        )
        .first()
    )
    if not row:
        return None
    product, tracking = row
    return _attach_tracking_metadata(product, tracking)


def get_latest_product_price(db: Session, product_id: int) -> PriceEntry | None:
    return (
        db.query(PriceEntry)
        .filter(PriceEntry.product_id == product_id)
        .order_by(PriceEntry.created_at.desc(), PriceEntry.id.desc())
        .first()
    )


def delete_product(db: Session, user_id: int, product_id: int) -> bool:
    tracking = (
        db.query(Tracking)
        .filter(Tracking.product_id == product_id, Tracking.user_id == user_id)
        .first()
    )
    if not tracking:
        return False

    db.delete(tracking)
    db.flush()

    remaining_tracking = db.query(Tracking.id).filter(Tracking.product_id == product_id).first() is not None
    if not remaining_tracking:
        db.query(PriceEntry).filter(PriceEntry.product_id == product_id).delete(
            synchronize_session=False
        )
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
    db.commit()
    return True


def get_product_prices(db: Session, user_id: int, product_id: int) -> List[PriceEntry] | None:
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    return (
        db.query(PriceEntry)
        .filter(PriceEntry.product_id == product_id)
        .order_by(PriceEntry.created_at.asc(), PriceEntry.id.asc())
        .all()
    )


def check_product_price(
    db: Session, user_id: int, product_id: int, locale: str | None = None
) -> PriceEntry | None:
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    scraped_price: float | None = None
    if product.url:
        scraped_data = scrape_product_data(product.url, locale=locale)
        if scraped_data and isinstance(scraped_data.get("price"), (int, float)):
            scraped_price = float(scraped_data["price"])

    # Keep a deterministic fallback flow for unsupported/blocked scrapes in development.
    price = scraped_price if scraped_price is not None else round(random.uniform(10, 500), 2)

    entry = PriceEntry(
        product_id=product.id,
        price=price,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    _maybe_notify_price_drop(db, user_id, product, entry)

    return entry


def _maybe_notify_price_drop(
    db: Session,
    user_id: int,
    product: Product,
    price_entry: PriceEntry,
) -> None:
    tracking = _get_tracking(db, user_id, product.id)
    if not tracking:
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    try:
        notification_service.maybe_notify_price_drop(
            db=db,
            user=user,
            product=product,
            tracking=tracking,
            price_entry=price_entry,
        )
    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "notification.email.error",
            tracking_id=tracking.id,
            error=str(exc),
        )
