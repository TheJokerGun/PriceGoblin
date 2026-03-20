from datetime import datetime, timezone
from unittest.mock import patch

from src.backend.models import NotificationLog, PriceEntry, Product, Tracking, User
from src.backend.services import notification_service

from .db_test_case import DatabaseTestCase


class NotificationServiceTests(DatabaseTestCase):
    def _create_user_product_tracking(self) -> tuple[User, Product, Tracking]:
        user = User(email="notify@example.com", password_hash="hashed")
        self.db.add(user)
        self.db.flush()

        product = Product(
            name="Tracked GPU",
            url="https://shop.example.com/product/notify-1",
            category="general",
            image_url=None,
        )
        self.db.add(product)
        self.db.flush()

        tracking = Tracking(
            user_id=user.id,
            product_id=product.id,
            is_active=True,
            source="shop.example.com",
            target_price=100.0,
        )
        self.db.add(tracking)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(product)
        self.db.refresh(tracking)
        return user, product, tracking

    @patch("src.backend.services.notification_service._send_teams_webhook", return_value=False)
    @patch("src.backend.services.notification_service._send_email", return_value=True)
    def test_maybe_notify_price_drop_creates_email_log(self, send_email_mock, _teams_mock) -> None:
        user, product, tracking = self._create_user_product_tracking()
        price_entry = PriceEntry(product_id=product.id, price=95.0)
        self.db.add(price_entry)
        self.db.commit()
        self.db.refresh(price_entry)

        notified = notification_service.maybe_notify_price_drop(
            db=self.db,
            user=user,
            product=product,
            tracking=tracking,
            price_entry=price_entry,
        )

        self.assertTrue(notified)
        send_email_mock.assert_called_once()

        logs = self.db.query(NotificationLog).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].channel, "email")
        self.assertEqual(logs[0].recipient, user.email)

    @patch("src.backend.services.notification_service._send_teams_webhook", return_value=False)
    @patch("src.backend.services.notification_service._send_email", return_value=True)
    def test_maybe_notify_price_drop_skips_when_price_above_target(self, send_email_mock, _teams_mock) -> None:
        user, product, tracking = self._create_user_product_tracking()
        price_entry = PriceEntry(product_id=product.id, price=120.0)
        self.db.add(price_entry)
        self.db.commit()
        self.db.refresh(price_entry)

        notified = notification_service.maybe_notify_price_drop(
            db=self.db,
            user=user,
            product=product,
            tracking=tracking,
            price_entry=price_entry,
        )

        self.assertFalse(notified)
        send_email_mock.assert_not_called()
        self.assertEqual(self.db.query(NotificationLog).count(), 0)

    @patch("src.backend.services.notification_service._send_teams_webhook", return_value=False)
    @patch("src.backend.services.notification_service._send_email", return_value=True)
    def test_maybe_notify_price_drop_respects_cooldown(self, send_email_mock, _teams_mock) -> None:
        user, product, tracking = self._create_user_product_tracking()

        first_price = PriceEntry(product_id=product.id, price=95.0)
        self.db.add(first_price)
        self.db.flush()
        self.db.add(
            NotificationLog(
                tracking_id=tracking.id,
                price_entry_id=first_price.id,
                channel="email",
                recipient=user.email,
                notified_price=95.0,
                target_price=tracking.target_price,
                notified_at=datetime.now(timezone.utc),
            )
        )

        new_price_entry = PriceEntry(product_id=product.id, price=95.0)
        self.db.add(new_price_entry)
        self.db.commit()
        self.db.refresh(new_price_entry)

        notified = notification_service.maybe_notify_price_drop(
            db=self.db,
            user=user,
            product=product,
            tracking=tracking,
            price_entry=new_price_entry,
        )

        self.assertFalse(notified)
        send_email_mock.assert_not_called()
        self.assertEqual(self.db.query(NotificationLog).count(), 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
