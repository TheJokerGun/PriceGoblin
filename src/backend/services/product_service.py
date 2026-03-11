from typing import List
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..models import PriceEntry, Product, Tracking
from ..schemas import (
    ProductCategorySelectionCreate,
    ProductCategorySelectionResponse,
    ProductCategorySelectionResult,
    ProductCreate,
    ScrapeProductResponse,
    ScrapeUrlRequest,
)
from datetime import datetime, timezone
import random
from ..scrapers.url_product_scraper import scrape_product_data
from ..price_utils import extract_price_value
from . import scraper_service


def _extract_price_value(value: str | float | int | None) -> float | None:
    return extract_price_value(value)


def _find_product_by_url(db: Session, url: str | None) -> Product | None:
    if not url:
        return None
    return db.query(Product).filter(Product.url == url).first()


def _infer_source_from_url(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.strip().lower()
    return host or None


def _attach_tracking_metadata(product: Product, tracking: Tracking | None) -> Product:
    if tracking is None:
        return product
    setattr(product, "tracking_id", tracking.id)
    setattr(product, "is_active", tracking.is_active)
    setattr(product, "source", tracking.source)
    setattr(product, "target_price", tracking.target_price)
    return product


def create_products_from_category_selection(
    db: Session, user_id: int, payload: ProductCategorySelectionCreate
) -> ProductCategorySelectionResponse:
    results: list[ProductCategorySelectionResult] = []

    for item in payload.items:
        name = (item.name or "").strip() or None
        url = (item.url or "").strip() or None
        category = (item.category or "").strip() or None
        image_url = (item.image_url or "").strip() or None
        source = (item.source or "").strip() or _infer_source_from_url(url)
        target_price = _extract_price_value(item.target_price)

        if not name and not url and not category:
            continue

        product = db.query(Product).filter(Product.url == url).first() if url else None
        created_product = False
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
            created_product = True
        else:
            if not product.name and name:
                product.name = name
            if not product.category and category:
                product.category = category
            if not product.image_url and image_url:
                product.image_url = image_url

        tracking = (
            db.query(Tracking)
            .filter(Tracking.user_id == user_id, Tracking.product_id == product.id)
            .first()
        )
        created_tracking = False
        if not tracking:
            tracking = Tracking(
                user_id=user_id,
                product_id=product.id,
                is_active=True,
                source=source,
                target_price=target_price,
            )
            db.add(tracking)
            db.flush()
            created_tracking = True
        else:
            tracking.is_active = True
            if source:
                tracking.source = source
            if target_price is not None:
                tracking.target_price = target_price

        seeded_price = None
        price_value = _extract_price_value(item.price)
        if price_value is not None:
            has_price_history = (
                db.query(PriceEntry.id).filter(PriceEntry.product_id == product.id).first() is not None
            )
            if created_product or not has_price_history:
                db.add(PriceEntry(product_id=product.id, price=price_value))
                seeded_price = price_value

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
    normalized_url = (scraped.url or url).strip()
    name = (scraped.name or "").strip() or None
    category = (scraped.category or "").strip() or None
    scraped_price = float(scraped.price) if isinstance(scraped.price, (int, float)) else None
    scraped_image_url = (scraped.image_url or "").strip() or None
    normalized_source = (source or "").strip() or _infer_source_from_url(normalized_url)

    # Match either the submitted URL or the final normalized URL to reduce duplicates.
    product = (
        db.query(Product)
        .filter(
            or_(
                Product.url == normalized_url,
                Product.url == url,
            )
        )
        .first()
    )

    created_new_product = False
    if not product:
        product = Product(
            name=name,
            url=normalized_url,
            category=category,
            image_url=scraped_image_url,
            created_at=datetime.now(timezone.utc),
        )
        db.add(product)
        db.flush()
        created_new_product = True
    else:
        if not product.name and name:
            product.name = name
        if not product.url and normalized_url:
            product.url = normalized_url
        if not product.category and category:
            product.category = category
        if not product.image_url and scraped_image_url:
            product.image_url = scraped_image_url

    if scraped_price is not None:
        has_price_history = (
            db.query(PriceEntry.id).filter(PriceEntry.product_id == product.id).first() is not None
        )
        if created_new_product or not has_price_history:
            db.add(PriceEntry(product_id=product.id, price=scraped_price))

    tracking = (
        db.query(Tracking)
        .filter(Tracking.user_id == user_id, Tracking.product_id == product.id)
        .first()
    )
    if not tracking:
        db.add(
            Tracking(
                user_id=user_id,
                product_id=product.id,
                is_active=True,
                source=normalized_source,
                target_price=target_price,
            )
        )
    else:
        tracking.is_active = True
        if normalized_source and not tracking.source:
            tracking.source = normalized_source
        if target_price is not None:
            tracking.target_price = target_price

    db.commit()
    db.refresh(product)
    if tracking is None:
        tracking = (
            db.query(Tracking)
            .filter(Tracking.user_id == user_id, Tracking.product_id == product.id)
            .first()
        )
    return _attach_tracking_metadata(product, tracking)


def create_product(
    db: Session, user_id: int, data: ProductCreate, locale: str | None = None
) -> Product:
    name = data.name
    url = data.url
    image_url = data.image_url
    scraped_price: float | None = None
    source = (data.source or "").strip() or _infer_source_from_url(url)

    # If a URL is provided, validate/scrape it and use scraped values as fallback.
    if data.url:
        try:
            scraped_data = scraper_service.scrape_url(
                ScrapeUrlRequest(url=data.url), locale=locale
            )
        except HTTPException:
            scraped_data = None
        if isinstance(scraped_data, ScrapeProductResponse):
            if not name:
                name = scraped_data.name
            url = scraped_data.url or data.url
            if isinstance(scraped_data.price, (int, float)):
                scraped_price = float(scraped_data.price)
            if not image_url and getattr(scraped_data, "image_url", None):
                image_url = scraped_data.image_url
            source = (data.source or "").strip() or _infer_source_from_url(url)

    product = _find_product_by_url(db, url)
    created_new_product = False
    if not product:
        product = Product(
            name=name,
            url=url,
            category=data.category,
            image_url=image_url,
            created_at=datetime.now(timezone.utc)
        )
        db.add(product)
        db.flush()
        created_new_product = True
    else:
        # Backfill missing metadata on an existing shared product.
        if not product.name and name:
            product.name = name
        if not product.category and data.category:
            product.category = data.category
        if not product.image_url and image_url:
            product.image_url = image_url

    # Persist first known price on create, or if an existing shared product has no history yet.
    if scraped_price is not None:
        has_price_history = (
            db.query(PriceEntry.id).filter(PriceEntry.product_id == product.id).first() is not None
        )
        if created_new_product or not has_price_history:
            db.add(PriceEntry(product_id=product.id, price=scraped_price))

    tracking = (
        db.query(Tracking)
        .filter(Tracking.user_id == user_id, Tracking.product_id == product.id)
        .first()
    )
    if not tracking:
        db.add(
            Tracking(
                user_id=user_id,
                product_id=product.id,
                is_active=True,
                source=source,
                target_price=data.target_price,
            )
        )
    else:
        tracking.is_active = True
        if source and not tracking.source:
            tracking.source = source
        if data.target_price is not None:
            tracking.target_price = data.target_price

    db.commit()
    db.refresh(product)
    if tracking is None:
        tracking = (
            db.query(Tracking)
            .filter(Tracking.user_id == user_id, Tracking.product_id == product.id)
            .first()
        )
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

    remaining_tracking = (
        db.query(Tracking.id).filter(Tracking.product_id == product_id).first() is not None
    )
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

    return db.query(PriceEntry).filter(
        PriceEntry.product_id == product_id
    ).all()


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

    price = scraped_price if scraped_price is not None else round(random.uniform(10, 500), 2)

    entry = PriceEntry(
        product_id=product.id,
        price=price
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry
