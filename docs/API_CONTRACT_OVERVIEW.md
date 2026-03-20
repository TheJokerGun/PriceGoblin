# PriceGoblin Backend API Contract (Current)

## Base
- Base URL: `http://<host>:<port>`
- API prefix: `/api`
- Content type: `application/json`
- Date/time fields: ISO-8601 timestamps (UTC)
- Database engine: SQLite (`db/pricegoblin.db`)

## Database Schema (Current)

### Tables

#### `users`
- `id` (INTEGER, PK, indexed)
- `email` (TEXT, unique, indexed, required)
- `password_hash` (TEXT, required)
- `created_at` (DATETIME with timezone intent, required)

#### `products`
- `id` (INTEGER, PK, indexed)
- `name` (TEXT, nullable)
- `url` (TEXT, nullable)
- `category` (TEXT, nullable)
- `created_at` (DATETIME with timezone intent, required)

#### `price_entries`
- `id` (INTEGER, PK, indexed)
- `product_id` (INTEGER, FK -> `products.id`, required)
- `price` (FLOAT, required)
- `created_at` (DATETIME with timezone intent, required)

#### `tracking`
- `id` (INTEGER, PK, indexed)
- `user_id` (INTEGER, FK -> `users.id`, required)
- `product_id` (INTEGER, FK -> `products.id`, required)
- `is_active` (BOOLEAN, default: `true`)
- `created_at` (DATETIME with timezone intent, required)

### Relationships
- One `users` row can have many `tracking` rows (`tracking.user_id`).
- One `products` row can have many `tracking` rows (`tracking.product_id`).
- One `products` row can have many `price_entries` rows (`price_entries.product_id`).
- `tracking` is the join table that links users to products and stores tracking state.

### Date/Time Storage and Delivery
- Timestamps are generated in backend code with `datetime.now(timezone.utc)`.
- SQLAlchemy columns use `DateTime(timezone=True)` for all `created_at` fields.
- In API responses, datetime values are serialized as ISO-8601 UTC strings, e.g.:
  - `2026-03-03T11:15:45.000000+00:00`
- Field mapping note:
  - `PriceResponse.checked_at` is sourced from DB column `price_entries.created_at`.

## Auth Model
- JWT bearer token is returned by login/register.
- Send token on protected endpoints:
  - `Authorization: Bearer <access_token>`
- Protected endpoints: all `/api/products/*`, `/api/tracking/*`, `/api/scrape/url`, `/api/scrape`
- Public endpoints: `/api/auth/register`, `/api/auth/login`, `/api/scrape/category`

## Common Error Shape
- FastAPI default:
```json
{ "detail": "..." }
```

## Endpoints

### Auth

#### `POST /api/auth/register`
Create a user and return a token.

Request:
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Success `201`:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Errors:
- `400` email already exists

#### `POST /api/auth/login`
Authenticate and return a token.

Request:
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Success `200`:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Errors:
- `401` invalid credentials

#### `GET /api/auth/me`
Get current authenticated user.

Success `200`:
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

---

### Products (Protected)

#### `POST /api/products`
Create or attach a product to the current user's tracking list.

Request:
```json
{
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "source": "alternate.de",
  "target_price": 450.0
}
```

Rules:
- At least one of `name`, `url`, `category` must be provided.

Success `200`:
```json
{
  "id": 10,
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "tracking_id": 55,
  "is_active": true,
  "source": "alternate.de",
  "target_price": 450.0,
  "created_at": "2026-03-03T10:12:30.123456+00:00"
}
```

Errors:
- `400` missing all identifying fields
- `401` unauthorized

#### `POST /api/products/bulk`
Bulk create/attach products from frontend-selected category results (no re-scrape).

Request:
```json
{
  "items": [
    {
      "name": "ELDEN RING",
      "url": "https://store.steampowered.com/app/1245620/ELDEN_RING/",
      "category": "games",
      "price": 59.99,
      "source": "steam",
      "target_price": 44.99
    },
    {
      "name": "ELDEN RING NIGHTREIGN Key kaufen Preisvergleich",
      "url": "https://www.allkeyshop.com/redirection/offer/...",
      "category": "games",
      "price": 10.35,
      "source": "GAMESEAL"
    }
  ]
}
```

Success `200`:
```json
{
  "count": 2,
  "data": [
    {
      "product_id": 101,
      "tracking_id": 55,
      "name": "ELDEN RING",
      "url": "https://store.steampowered.com/app/1245620/ELDEN_RING/",
      "category": "games",
      "source": "steam",
      "target_price": 44.99,
      "is_active": true,
      "created_product": true,
      "created_tracking": true,
      "seeded_price": 59.99
    }
  ]
}
```

Errors:
- `400` items must not be empty
- `401` unauthorized

#### `GET /api/products`
List products tracked by current user.

Success `200`:
```json
[
  {
    "id": 10,
    "name": "RTX 4080",
    "url": "https://example.com/p/123",
    "category": null,
    "tracking_id": 55,
    "is_active": true,
    "source": "alternate.de",
    "target_price": 450.0,
    "created_at": "2026-03-03T10:12:30.123456+00:00"
  }
]
```

#### `GET /api/products/{product_id}`
Get one tracked product by id (current user tracking enforced).

Success `200`:
```json
{
  "id": 10,
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "tracking_id": 55,
  "is_active": true,
  "source": "alternate.de",
  "target_price": 450.0,
  "created_at": "2026-03-03T10:12:30.123456+00:00"
}
```

Errors:
- `404` product not found
- `401` unauthorized

#### `DELETE /api/products/{product_id}`
Untrack one product for the current user.
If no users track the product afterward, the product and its price history are removed.

Success `200`:
```json
{ "detail": "Product untracked successfully" }
```

Errors:
- `404` product not found
- `401` unauthorized

#### `GET /api/products/{product_id}/prices`
Get all stored historical prices for a product (DB only).

Success `200`:
```json
[
  {
    "id": 301,
    "price": 499.99,
    "checked_at": "2026-03-03T10:20:15.000000+00:00"
  },
  {
    "id": 322,
    "price": 479.99,
    "checked_at": "2026-03-03T11:15:45.000000+00:00"
  }
]
```

Errors:
- `404` product not found
- `401` unauthorized

#### `GET /api/products/{product_id}/current-price`
Get latest stored price entry for a product (DB only, no scraping call).

Success `200`:
```json
{
  "id": 322,
  "price": 479.99,
  "checked_at": "2026-03-03T11:15:45.000000+00:00"
}
```

Errors:
- `404` product not found
- `404` no stored price found for product
- `401` unauthorized

#### `POST /api/products/{product_id}/check-price`
Actively checks current price (scrape path), stores it in DB, and returns created price entry.

Success `200`:
```json
{
  "id": 333,
  "price": 469.99,
  "checked_at": "2026-03-03T12:00:00.000000+00:00"
}
```

Errors:
- `404` product not found
- `401` unauthorized

#### `DELETE /api/tracking/{tracking_id}`
Delete a tracking entry owned by the authenticated user.

Success `200`:
```json
{
  "detail": "Tracking entry deleted successfully"
}
```

Errors:
- `404` tracking entry not found
- `401` unauthorized

#### `GET /api/tracking`
List tracking entries for the authenticated user.

Success `200`:
```json
[
  {
    "id": 44,
    "user_id": 1,
    "product_id": 12,
    "is_active": true,
    "source": "steam",
    "target_price": 44.99,
    "created_at": "2026-03-04T09:00:00.000000+00:00"
  }
]
```

Errors:
- `401` unauthorized

#### `PATCH /api/tracking/{tracking_id}/active`
Set a tracking entry active/inactive.  
If `is_active` is omitted or `null`, the value is toggled.

Request:
```json
{
  "is_active": false
}
```

Success `200`:
```json
{
  "id": 44,
  "user_id": 1,
  "product_id": 12,
  "is_active": false,
  "source": "steam",
  "target_price": 44.99,
  "created_at": "2026-03-04T09:00:00.000000+00:00"
}
```

Errors:
- `404` tracking entry not found
- `401` unauthorized

#### `PATCH /api/tracking/{tracking_id}/target-price`
Set or clear the user's target buy price for this tracking entry.

Request:
```json
{
  "target_price": 39.99
}
```

Use `null` to clear:
```json
{
  "target_price": null
}
```

Success `200`:
```json
{
  "id": 44,
  "user_id": 1,
  "product_id": 12,
  "is_active": true,
  "source": "steam",
  "target_price": 39.99,
  "created_at": "2026-03-04T09:00:00.000000+00:00"
}
```

Errors:
- `404` tracking entry not found
- `401` unauthorized

---

### Scraping

#### `POST /api/scrape/url`
Scrape one product URL, then persist into:
- `products` (create if URL not present, otherwise reuse/update),
- `tracking` for current user (create or reactivate),
- `price_entries` seed on first known price for that product.

Auth required.

Request:
```json
{
  "url": "https://example.com/p/123",
  "target_price": 450.0
}
```

Success `200`:
```json
{
  "type": "product",
  "id": 10,
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "created_at": "2026-03-03T10:00:00.000000+00:00",
  "price": 499.99
}
```

Errors:
- `400` scrape failed
- `401` unauthorized

#### `POST /api/scrape/category`
Scrape category candidates (selection list for frontend).  
Use this before product creation in category flow.

Request:
```json
{
  "category": "games",
  "name": "elden ring",
  "limit": 10
}
```

Success `200`:
```json
{
  "type": "category",
  "category": "games",
  "count": 3,
  "data": [
    {
      "name": "ELDEN RING",
      "price": 59.99,
      "source": "steam",
      "url": "https://store.steampowered.com/app/1245620/ELDEN_RING/"
    },
    {
      "name": "ELDEN RING NIGHTREIGN Key kaufen Preisvergleich",
      "price": 10.35,
      "source": "GAMESEAL",
      "url": "https://www.allkeyshop.com/redirection/offer/..."
    }
  ]
}
```

Supported category keys (current implementation): `general`, `games`, `cards`.
`limit` is clamped to `1..50` (default `10`).

Errors:
- `400` scrape failed
- `500` invalid category scraper output format

#### `POST /api/scrape`
Legacy combined endpoint (backward-compatible).  
Prefer `/api/scrape/url` and `/api/scrape/category` for new frontend flow.
