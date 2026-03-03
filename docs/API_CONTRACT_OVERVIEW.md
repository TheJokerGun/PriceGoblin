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
- `user_id` (INTEGER, FK -> `users.id`, required)
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
- `url` (TEXT, nullable)
- `created_at` (DATETIME with timezone intent, required)

### Relationships
- One `users` row can have many `products` rows (`products.user_id`).
- One `products` row can have many `price_entries` rows (`price_entries.product_id`).
- `tracking` links `users` and `products` for tracking state.

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
- Protected endpoints: all `/api/products/*`
- Public endpoints: `/api/auth/register`, `/api/auth/login`, `/api/scrape`

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
Create a product.

Request:
```json
{
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null
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
  "created_at": "2026-03-03T10:12:30.123456+00:00"
}
```

Errors:
- `400` missing all identifying fields
- `401` unauthorized

#### `GET /api/products`
List all products of current user.

Success `200`:
```json
[
  {
    "id": 10,
    "name": "RTX 4080",
    "url": "https://example.com/p/123",
    "category": null,
    "created_at": "2026-03-03T10:12:30.123456+00:00"
  }
]
```

#### `GET /api/products/{product_id}`
Get one product by id (current user ownership enforced).

Success `200`:
```json
{
  "id": 10,
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "created_at": "2026-03-03T10:12:30.123456+00:00"
}
```

Errors:
- `404` product not found
- `401` unauthorized

#### `DELETE /api/products/{product_id}`
Delete one product.

Success `200`:
```json
{ "detail": "Product deleted successfully" }
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

---

### Scraping (Public)

#### `POST /api/scrape`
Scrape either by `url` or by `category`.

Request (product/url mode):
```json
{
  "url": "https://example.com/p/123"
}
```

Request (category mode):
```json
{
  "category": "graphics-cards"
}
```

Rules:
- Provide exactly one of `url` or `category`.
- For category mode, `name` is used as the search query term.

Success `200` (url mode):
```json
{
  "type": "product",
  "id": 1,
  "name": "RTX 4080",
  "url": "https://example.com/p/123",
  "category": null,
  "created_at": "2026-03-03T10:00:00.000000+00:00",
  "price": 499.99
}
```

Success `200` (category mode):
```json
{
  "type": "category",
  "category": "graphics-cards",
  "count": 2,
  "data": [
    {
      "name": "GPU A",
      "price": "499,99 €",
      "source": "idealo",
      "url": "https://example.com/product-a"
    },
    {
      "name": "GPU B",
      "price": 529.99,
      "source": "geizhals",
      "url": "https://example.com/product-b"
    }
  ]
}
```

Errors:
- `400` invalid input or scrape failure
- `500` invalid category scraper output format

## Notes for Frontend
- Use `GET /api/products/{product_id}/current-price` to show the latest known value without triggering a new scrape.
- Use `POST /api/products/{product_id}/check-price` only when you intentionally want a fresh fetch + DB write.
