# PriceGoblin TODO / Next Steps

Last updated: 2026-03-03

## 1) Immediate Next Tasks (High Priority)

- [ ] Add automated tests for current API endpoints:
  - auth (`register`, `login`, `me`)
  - products (`create`, `list`, `get by id`, `delete`)
  - prices (`history`, `current-price`, `check-price`)
  - scrape endpoint (`url` and `category`)
- [ ] Add fixture test data for:
  - one user with products
  - products with and without stored price entries
  - unauthorized requests
- [ ] Define clear error behavior for frontend:
  - `404` with no stored price
  - scrape failures (`400`)
  - invalid token (`401`)

## 2) URL Scraping Reliability (High Priority)

- [ ] Validate real product URLs for:
  - Cyberport
  - Alternate
  - Mindfactory
  - Notebooksbilliger
- [ ] For each site, verify and tune selectors for:
  - product title
  - product price
- [ ] Add site-specific fallback logic when main selectors fail.
- [ ] Add debug capture on scrape failure:
  - save response HTML for BS4
  - save screenshot + HTML snippet for Playwright
- [ ] Track scrape success rate per site in logs.

## 3) Category Scraping (Now: Rough Structure -> Next: Useful Data)

- [ ] Keep category naming consistent:
  - `general`
  - `games`
  - `cards`
- [ ] Use `ScrapeRequest.name` as search query for category mode in frontend calls.
- [ ] Validate providers and selectors:
  - `general`: Idealo, Geizhals
  - `games`: Steam, KeyforSteam
  - `cards`: decide final source(s), currently scaffolded with Cardmarket links
- [ ] Normalize category results:
  - unify `price` into numeric value where possible
  - keep original text as optional field if needed
  - always include `source` and `url`
- [ ] Add ranking logic (top results):
  - sort by best price first (where parseable)
  - fallback sort by source/name

## 4) Data Model / Backend Improvements

- [ ] Decide and implement a `current_price` strategy:
  - keep only latest in `products` table, or
  - continue using latest from `price_entries` (current behavior)
- [ ] Add DB indexes for likely frequent queries:
  - `products.user_id`
  - `price_entries.product_id`
  - `price_entries.created_at`
- [ ] Add migration workflow (Alembic) instead of implicit auto-create only.
- [ ] Validate if `tracking` table should be integrated into active endpoint flows now.

## 5) API Contract + Developer Experience

- [ ] Keep `docs/API_CONTRACT_OVERVIEW.md` in sync after every endpoint change.
- [ ] Add example requests/responses for common frontend flows:
  - create product -> get current-price -> check-price -> refresh current-price
- [ ] Add OpenAPI screenshot/export for submission documentation.
- [ ] Add a short "how to run backend locally" section in README.

## 6) Frontend Integration Tasks

- [ ] Product detail page:
  - call `GET /api/products/{product_id}`
  - call `GET /api/products/{product_id}/current-price`
- [ ] Product list page:
  - avoid scraping on initial load
  - show cached/latest DB value first
- [ ] Manual refresh button:
  - call `POST /api/products/{product_id}/check-price`
  - update UI with returned value
- [ ] Add clear empty states:
  - no products
  - no stored price yet
  - scrape failed

## 7) Security / Stability

- [ ] Add request rate limiting for scrape endpoints.
- [ ] Add timeout/retry policy per provider.
- [ ] Add lightweight input validation for URLs/categories in scrape requests.
- [ ] Ensure secrets (`SECRET_KEY`) are set in deployment and not committed.

## 8) School Project Deliverables

- [ ] Define MVP boundary for presentation:
  - auth + product tracking + stored current price + one working scrape path
- [ ] Prepare demo script (5-10 minutes):
  - register/login
  - add product
  - show current stored price
  - trigger check-price
  - show updated history
- [ ] Prepare architecture slide:
  - FastAPI routes
  - services
  - scrapers
  - SQLite data flow
- [ ] Prepare known limitations slide:
  - Cloudflare/bot blocking
  - site selector fragility
  - category data quality still iterative

## Suggested Work Order (Pragmatic)

1. Tests for existing endpoints and basic scrape flow
2. One fully reliable URL site scraper end-to-end
3. Frontend integration with `current-price` + `check-price`
4. Category providers tuning
5. Submission polish (docs + demo script + slides)
