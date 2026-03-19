from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import os
from typing import Any

from dotenv import load_dotenv
import httpx
from sqlalchemy.orm import Session

from ..logging_utils import configure_logging, log_event
from ..models import NotificationLog, PriceEntry, Product, Tracking, User

load_dotenv()

logger = configure_logging()

DEFAULT_COOLDOWN_HOURS = 24
DEFAULT_PRICE_EPSILON = 0.01


@dataclass(frozen=True)
class EmailConfig:
    provider: str
    from_email: str
    reply_to: str | None
    api_key: str | None
    message_stream: str | None


def _get_email_config() -> EmailConfig | None:
    provider = os.getenv("EMAIL_PROVIDER", "").strip().lower()
    from_email = os.getenv("EMAIL_FROM", "").strip()
    if not provider or not from_email:
        return None

    reply_to = os.getenv("EMAIL_REPLY_TO", "").strip() or None
    api_key = None
    message_stream = None
    if provider == "resend":
        api_key = os.getenv("RESEND_API_KEY", "").strip() or None
    elif provider == "sendgrid":
        api_key = os.getenv("SENDGRID_API_KEY", "").strip() or None
    elif provider == "postmark":
        api_key = os.getenv("POSTMARK_SERVER_TOKEN", "").strip() or None
        message_stream = os.getenv("POSTMARK_MESSAGE_STREAM", "").strip() or None
    else:
        return None

    if not api_key:
        return None

    return EmailConfig(
        provider=provider,
        from_email=from_email,
        reply_to=reply_to,
        api_key=api_key,
        message_stream=message_stream,
    )


def _cooldown_hours() -> int:
    value = os.getenv("NOTIFICATION_COOLDOWN_HOURS", "").strip()
    if not value:
        return DEFAULT_COOLDOWN_HOURS
    try:
        hours = int(value)
        return hours if hours >= 0 else DEFAULT_COOLDOWN_HOURS
    except ValueError:
        return DEFAULT_COOLDOWN_HOURS


def _price_epsilon() -> float:
    value = os.getenv("NOTIFICATION_PRICE_EPSILON", "").strip()
    if not value:
        return DEFAULT_PRICE_EPSILON
    try:
        epsilon = float(value)
        return epsilon if epsilon >= 0 else DEFAULT_PRICE_EPSILON
    except ValueError:
        return DEFAULT_PRICE_EPSILON


def _format_price(value: float) -> str:
    return f"{value:.2f}"


def _build_price_drop_email(
    product: Product,
    price_entry: PriceEntry,
    target_price: float,
) -> tuple[str, str, str | None]:
    name = product.name or "Tracked item"
    current_price = _format_price(price_entry.price)
    target = _format_price(target_price)
    url = (product.url or "").strip()

    subject = f"Price alert: {name} now {current_price}"
    text_lines = [
        "Good news - your tracked item hit the target price.",
        "",
        f"Product: {name}",
        f"Current price: {current_price}",
        f"Target price: {target}",
    ]
    if url:
        text_lines.append(f"Link: {url}")
    text_lines.append("")
    text_lines.append("PriceGoblin")
    text_body = "\n".join(text_lines)

    html_body = None
    if url:
        html_body = (
            "<p>Good news - your tracked item hit the target price.</p>"
            f"<p><strong>Product:</strong> {name}<br/>"
            f"<strong>Current price:</strong> {current_price}<br/>"
            f"<strong>Target price:</strong> {target}<br/>"
            f"<strong>Link:</strong> <a href=\"{url}\">{url}</a></p>"
            "<p>PriceGoblin</p>"
        )

    return subject, text_body, html_body


def _send_resend_email(config: EmailConfig, to_email: str, subject: str, text: str, html: str | None) -> None:
    payload: dict[str, Any] = {
        "from": config.from_email,
        "to": [to_email],
        "subject": subject,
        "text": text,
    }
    if html:
        payload["html"] = html
    if config.reply_to:
        payload["reply_to"] = config.reply_to

    headers = {"Authorization": f"Bearer {config.api_key}"}
    with httpx.Client(timeout=10) as client:
        response = client.post("https://api.resend.com/emails", json=payload, headers=headers)
        response.raise_for_status()


def _send_sendgrid_email(config: EmailConfig, to_email: str, subject: str, text: str, html: str | None) -> None:
    content = [{"type": "text/plain", "value": text}]
    if html:
        content.append({"type": "text/html", "value": html})

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": config.from_email},
        "subject": subject,
        "content": content,
    }
    if config.reply_to:
        payload["reply_to"] = {"email": config.reply_to}

    headers = {"Authorization": f"Bearer {config.api_key}"}
    with httpx.Client(timeout=10) as client:
        response = client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
        response.raise_for_status()


def _send_postmark_email(config: EmailConfig, to_email: str, subject: str, text: str, html: str | None) -> None:
    payload = {
        "From": config.from_email,
        "To": to_email,
        "Subject": subject,
        "TextBody": text,
    }
    if html:
        payload["HtmlBody"] = html
    if config.reply_to:
        payload["ReplyTo"] = config.reply_to
    if config.message_stream:
        payload["MessageStream"] = config.message_stream

    headers = {"X-Postmark-Server-Token": config.api_key}
    with httpx.Client(timeout=10) as client:
        response = client.post("https://api.postmarkapp.com/email", json=payload, headers=headers)
        response.raise_for_status()


def _send_email(
    to_email: str,
    subject: str,
    text: str,
    html: str | None,
) -> bool:
    config = _get_email_config()
    if config is None:
        log_event(logger, logging.INFO, "notification.email.disabled")
        return False

    try:
        if config.provider == "resend":
            _send_resend_email(config, to_email, subject, text, html)
        elif config.provider == "sendgrid":
            _send_sendgrid_email(config, to_email, subject, text, html)
        elif config.provider == "postmark":
            _send_postmark_email(config, to_email, subject, text, html)
        else:
            log_event(logger, logging.WARNING, "notification.email.unsupported_provider", provider=config.provider)
            return False
        return True
    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "notification.email.failed",
            provider=config.provider,
            error=str(exc),
        )
        return False


def _build_teams_message_card(
    user: User,
    product: Product,
    price_entry: PriceEntry,
    target_price: float,
) -> dict[str, Any]:
    name = product.name or "Tracked item"
    current_price = _format_price(price_entry.price)
    target = _format_price(target_price)
    url = (product.url or "").strip()
    facts = [
        {"name": "User", "value": user.email},
        {"name": "Current price", "value": current_price},
        {"name": "Target price", "value": target},
    ]
    if url:
        facts.append({"name": "Link", "value": url})

    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "PriceGoblin price alert",
        "themeColor": "0076D7",
        "title": f"Price alert: {name}",
        "sections": [
            {
                "facts": facts,
                "markdown": True,
            }
        ],
    }


def _send_teams_webhook(payload: dict[str, Any]) -> bool:
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return False

    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
        return True
    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "notification.teams.failed",
            error=str(exc),
        )
        return False


def _latest_notification(db: Session, tracking_id: int) -> NotificationLog | None:
    return (
        db.query(NotificationLog)
        .filter(NotificationLog.tracking_id == tracking_id)
        .order_by(NotificationLog.notified_at.desc(), NotificationLog.id.desc())
        .first()
    )


def _should_notify_again(price: float, last_log: NotificationLog) -> bool:
    epsilon = _price_epsilon()
    if price < last_log.notified_price - epsilon:
        return True

    cooldown = _cooldown_hours()
    if cooldown <= 0:
        return True

    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown)
    return last_log.notified_at < cutoff


def maybe_notify_price_drop(
    db: Session,
    user: User,
    product: Product,
    tracking: Tracking,
    price_entry: PriceEntry,
) -> bool:
    if not tracking.is_active:
        return False
    if tracking.target_price is None:
        return False
    if price_entry.price > tracking.target_price:
        return False

    last_log = _latest_notification(db, tracking.id)
    if last_log and not _should_notify_again(price_entry.price, last_log):
        log_event(
            logger,
            logging.INFO,
            "notification.email.skipped",
            tracking_id=tracking.id,
            price=price_entry.price,
            target_price=tracking.target_price,
        )
        return False

    subject, text, html = _build_price_drop_email(product, price_entry, tracking.target_price)
    email_sent = _send_email(user.email, subject, text, html)
    teams_payload = _build_teams_message_card(user, product, price_entry, tracking.target_price)
    teams_sent = _send_teams_webhook(teams_payload)

    if not email_sent and not teams_sent:
        return False

    if email_sent:
        log_entry = NotificationLog(
            tracking_id=tracking.id,
            price_entry_id=price_entry.id,
            channel="email",
            recipient=user.email,
            notified_price=price_entry.price,
            target_price=tracking.target_price,
            notified_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        log_event(
            logger,
            logging.INFO,
            "notification.email.sent",
            tracking_id=tracking.id,
            price=price_entry.price,
            target_price=tracking.target_price,
        )

    if teams_sent:
        log_entry = NotificationLog(
            tracking_id=tracking.id,
            price_entry_id=price_entry.id,
            channel="teams",
            recipient="teams_webhook",
            notified_price=price_entry.price,
            target_price=tracking.target_price,
            notified_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        log_event(
            logger,
            logging.INFO,
            "notification.teams.sent",
            tracking_id=tracking.id,
            price=price_entry.price,
            target_price=tracking.target_price,
        )

    db.commit()
    return True
