import json
import logging
import os
from typing import Any

from fastapi import Request

LOGGER_NAME = "pricegoblin.api"
MAX_BODY_CHARS = 2_000
MAX_BODY_BYTES = 25_000
MAX_ERROR_DETAIL_CHARS = 400
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "authorization",
    "cookie",
}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_log_mode() -> str:
    mode = os.getenv("API_LOG_MODE", "compact").strip().lower()
    if mode not in {"compact", "verbose"}:
        return "compact"
    return mode


def should_log_request_received(request: Request) -> bool:
    mode = get_log_mode()
    if mode == "verbose":
        return True

    if request.method == "OPTIONS":
        return False

    # In compact mode, log incoming payloads for mutating requests only.
    return request.method in {"POST", "PUT", "PATCH", "DELETE"}


def should_log_request_completed(request: Request, status_code: int) -> bool:
    mode = get_log_mode()
    if mode == "verbose":
        return True

    if request.method == "OPTIONS":
        return False

    if status_code >= 400:
        return True

    # In compact mode, keep success logs only for mutating requests.
    return request.method in {"POST", "PUT", "PATCH", "DELETE"}


def configure_logging() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    log_level_name = os.getenv("API_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)
    logger.propagate = False

    if not _env_bool("UVICORN_ACCESS_LOG", False):
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    if not _env_bool("SQL_ECHO", False):
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logger


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, default=str))


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = _redact(item)
        return sanitized
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _truncate(text: str, max_chars: int = MAX_BODY_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...<truncated>"


def format_exception_detail(exc: Exception, max_chars: int = MAX_ERROR_DETAIL_CHARS) -> str:
    return _truncate(str(exc), max_chars=max_chars)


async def get_sanitized_request_body(request: Request) -> Any:
    content_type = request.headers.get("content-type", "").lower()

    if "multipart/form-data" in content_type:
        return "<multipart body omitted>"

    body_bytes = await request.body()
    if not body_bytes:
        return None

    if len(body_bytes) > MAX_BODY_BYTES:
        return f"<body omitted: {len(body_bytes)} bytes>"

    if "application/json" in content_type:
        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
            return _redact(parsed)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "<invalid json body>"

    try:
        return _truncate(body_bytes.decode("utf-8"))
    except UnicodeDecodeError:
        return "<non-text body omitted>"


def get_request_headers(request: Request) -> dict[str, str | None]:
    authorization = request.headers.get("authorization")
    if authorization:
        authorization = "***REDACTED***"
    return {
        "content_type": request.headers.get("content-type"),
        "user_agent": request.headers.get("user-agent"),
        "authorization": authorization,
    }


def extract_validation_expectations(errors: list[dict[str, Any]]) -> list[str]:
    expected: list[str] = []
    for error in errors:
        loc = ".".join(str(part) for part in error.get("loc", []))
        if loc:
            expected.append(loc)
    # Keep order and remove duplicates.
    return list(dict.fromkeys(expected))
