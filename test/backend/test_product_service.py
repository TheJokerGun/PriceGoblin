from datetime import datetime, timezone
from unittest.mock import patch

from src.backend.models import PriceEntry, Product, Tracking, User
from src.backend.schemas import (
    ProductCategorySelectionCreate,
    ProductCreate,
    ProductSelectionItem,
    ScrapeProductResponse,
)
from src.backend.services import product_service

from .db_test_case import DatabaseTestCase


class ProductServiceTests(DatabaseTestCase):
    def _create_user(self, email: str) -> User:
        user = User(email=email, password_hash="hashed-password", locale="de-DE")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def test_create_product_without_url_creates_tracking(self) -> None:
        user = self._create_user("alice@example.com")

        product = product_service.create_product(
            self.db,
            user.id,
            ProductCreate(
                name="RTX 4080",
                url=None,
                category="general",
                image_url=None,
                source=None,
                target_price=499.99,
            ),
        )

        self.assertEqual(product.name, "RTX 4080")
        self.assertEqual(getattr(product, "tracking_id", None), 1)

        tracking = self.db.query(Tracking).filter(Tracking.user_id == user.id).one()
        self.assertEqual(tracking.product_id, product.id)
        self.assertEqual(tracking.target_price, 499.99)
        self.assertTrue(tracking.is_active)

    def test_bulk_category_selection_reuses_product_and_single_seed_price(self) -> None:
        user = self._create_user("bob@example.com")
        shared_url = "https://shop.example.com/product/gpu-1"

        first = product_service.create_products_from_category_selection(
            self.db,
            user.id,
            ProductCategorySelectionCreate(
                items=[
                    ProductSelectionItem(
                        name="GPU Model 1",
                        url=shared_url,
                        category="general",
                        price="199,99 EUR",
                        source=None,
                        target_price=180.0,
                    )
                ]
            ),
        )
        second = product_service.create_products_from_category_selection(
            self.db,
            user.id,
            ProductCategorySelectionCreate(
                items=[
                    ProductSelectionItem(
                        name="GPU Model 1 Updated",
                        url=shared_url,
                        category="general",
                        price="149,99 EUR",
                        source="manual-source",
                        target_price=175.0,
                    )
                ]
            ),
        )

        self.assertEqual(first.count, 1)
        self.assertEqual(second.count, 1)
        self.assertEqual(self.db.query(Product).count(), 1)
        self.assertEqual(self.db.query(Tracking).count(), 1)
        # Seed price is inserted only once when history already exists.
        self.assertEqual(self.db.query(PriceEntry).count(), 1)

        tracking = self.db.query(Tracking).one()
        self.assertEqual(tracking.source, "manual-source")
        self.assertEqual(tracking.target_price, 175.0)

    @patch("src.backend.services.product_service.scraper_service.scrape_url")
    def test_delete_product_keeps_shared_product_until_last_tracking_removed(self, scrape_url_mock) -> None:
        now = datetime.now(timezone.utc)
        scrape_url_mock.return_value = ScrapeProductResponse(
            name="Shared Product",
            url="https://shop.example.com/product/shared-1",
            category="general",
            created_at=now,
            price=199.99,
            image_url="https://shop.example.com/product/shared-1.jpg",
        )

        user_one = self._create_user("charlie@example.com")
        user_two = self._create_user("dora@example.com")
        payload = ProductCreate(
            name=None,
            url="https://shop.example.com/product/shared-1",
            category=None,
            image_url=None,
            source=None,
            target_price=150.0,
        )

        first_product = product_service.create_product(self.db, user_one.id, payload)
        second_product = product_service.create_product(self.db, user_two.id, payload)
        self.assertEqual(first_product.id, second_product.id)

        deleted = product_service.delete_product(self.db, user_one.id, first_product.id)
        self.assertTrue(deleted)
        self.assertIsNotNone(
            self.db.query(Product).filter(Product.id == first_product.id).first()
        )
        self.assertEqual(
            self.db.query(Tracking).filter(Tracking.product_id == first_product.id).count(),
            1,
        )

        deleted_last = product_service.delete_product(self.db, user_two.id, first_product.id)
        self.assertTrue(deleted_last)
        self.assertIsNone(
            self.db.query(Product).filter(Product.id == first_product.id).first()
        )
        self.assertEqual(
            self.db.query(PriceEntry).filter(PriceEntry.product_id == first_product.id).count(),
            0,
        )

    @patch("src.backend.services.product_service.notification_service.maybe_notify_price_drop")
    @patch("src.backend.services.product_service.random.uniform", return_value=42.424)
    def test_check_product_price_uses_fallback_when_scrape_missing(
        self,
        random_uniform_mock,
        notify_mock,
    ) -> None:
        user = self._create_user("eve@example.com")
        product = product_service.create_product(
            self.db,
            user.id,
            ProductCreate(
                name="No URL Product",
                url=None,
                category="general",
                image_url=None,
                source=None,
                target_price=100.0,
            ),
        )

        entry = product_service.check_product_price(self.db, user.id, product.id)

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.price, 42.42)
        random_uniform_mock.assert_called_once_with(10, 500)
        notify_mock.assert_called_once()


if __name__ == "__main__":
    import unittest

    unittest.main()
