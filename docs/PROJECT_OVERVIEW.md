# PriceGoblin Project Overview

## What This Project Is
PriceGoblin is a backend service that helps users track product prices across supported retailers and marketplaces. It accepts either direct product URLs or a category search, scrapes product metadata (name, price, image), stores products and tracking preferences, and exposes that data via a JSON API.

## Core Concepts
- **Product**: Unique product entry shared across users. Fields include `name`, `url`, `category`, `image_url`, and timestamps.
- **Tracking**: Join table between users and products. Stores `is_active`, `source`, and `target_price` for notifications.
- **PriceEntry**: Time-series price history for a product.
- **User**: Account owner of tracking entries.

## Main Flows
- **URL scrape**
  - Input: product URL
  - Output: scraped product metadata + latest price
  - Effect: product is created/updated, tracking row is created/updated, and a price entry is stored.

- **Category scrape**
  - Input: category + query
  - Output: list of candidate products with price + image
  - Effect: no DB writes; frontend selects items and then submits a bulk create request.

## Scraping Strategy
- **URL scraping** uses a fast BeautifulSoup pass first, then falls back to Playwright for dynamic sites or bot protections.
- **Category scraping** uses a mix of provider-specific and generic selectors and returns a small candidate set for selection.
- **Images** are preferred from `og:image` or JSON-LD `image` fields, with `img` fallback when needed.

## Logging System
The API uses structured JSON logs for each request and internal scraping events. Logs include a `request_id` and are emitted at consistent lifecycle points.

### Request Logging Behavior
- **`request.received`** is emitted based on `API_LOG_MODE` (compact vs verbose).
- **`request.completed`** is emitted based on request method and response status.
- Validation and exception handlers emit dedicated structured logs with redacted/sanitized payloads.

### Log Redaction & Truncation
- Sensitive keys (`authorization`, `password`, `token`, etc.) are redacted.
- Request bodies are capped at 25 KB and truncated to 2,000 chars.
- Error details are truncated to 400 chars.

## Environment Variables
These control logging and SQL output. All of them are optional.

- `API_LOG_MODE`
  - `compact` (default): logs only mutating requests and failures.
  - `verbose`: logs every request and response.

- `API_LOG_LEVEL`
  - Default: `INFO`
  - Common options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - Controls the main application logger (`pricegoblin.api`).

- `SQL_ECHO`
  - `true` enables SQLAlchemy engine logging.
  - `false` (default) suppresses SQL logs.

- `UVICORN_ACCESS_LOG`
  - `true` enables Uvicorn access logs.
  - `false` (default) suppresses access logs so you rely on structured API logs.

## Debugging Tips
- For deeper request context, set:
  - `API_LOG_MODE=verbose`
  - `API_LOG_LEVEL=DEBUG`
- For SQL visibility, set:
  - `SQL_ECHO=true`
- For raw access logs, set:
  - `UVICORN_ACCESS_LOG=true`

## Data Storage
- SQLite database at `db/pricegoblin.db`
- Schema migrations are handled at startup in `src/backend/database.py`.

## Useful Entry Points
- API routes: `src/backend/routes/`
- Scrapers: `src/backend/scrapers/`
- Logging: `src/backend/logging_utils.py`
- DB schema: `src/backend/models.py`
