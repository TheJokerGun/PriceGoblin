# Endpoint Testing Guide (Without Frontend)

This guide lets you test your backend directly via Swagger or curl.

## 1) Swagger UI (Recommended for manual checks)

1. Start backend (example):
   - `uv run fastapi dev src/backend/main.py`
2. Open Swagger:
   - `http://127.0.0.1:8000/docs`
3. Click **Authorize**.
4. First call `POST /api/auth/login` and copy `access_token`.
5. Click **Authorize** and paste the token into the Bearer auth dialog.
6. Test protected endpoints like:
   - `GET /api/products`
   - `GET /api/products/{product_id}`
   - `GET /api/products/{product_id}/current-price`
   - `POST /api/products/{product_id}/check-price`

## 2) Curl Testing Flow

Set base URL:

```bash
BASE_URL="http://127.0.0.1:8000"
```

Get token (JSON login):

```bash
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD"}' \
  | jq -r '.access_token')

echo "$TOKEN"
```

Call protected endpoint:

```bash
curl -s "$BASE_URL/api/products" \
  -H "Authorization: Bearer $TOKEN"
```

Create product:

```bash
curl -s -X POST "$BASE_URL/api/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"RTX 4080","url":"https://www.cyberport.de/?DEMO","source":"cyberport.de","target_price":449.99}'
```

Bulk create products from selected category candidates (no re-scrape):

```bash
curl -s -X POST "$BASE_URL/api/products/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items":[
      {"name":"ELDEN RING","url":"https://store.steampowered.com/app/1245620/ELDEN_RING/","category":"games","price":59.99,"source":"steam","target_price":44.99},
      {"name":"ELDEN RING NIGHTREIGN Key kaufen Preisvergleich","url":"https://www.allkeyshop.com/redirection/offer/...","category":"games","price":10.35,"source":"GAMESEAL"}
    ]
  }'
```

Get one product:

```bash
curl -s "$BASE_URL/api/products/1" \
  -H "Authorization: Bearer $TOKEN"
```

Get current stored price (DB only):

```bash
curl -s "$BASE_URL/api/products/1/current-price" \
  -H "Authorization: Bearer $TOKEN"
```

Trigger fresh scrape + store price:

```bash
curl -s -X POST "$BASE_URL/api/products/1/check-price" \
  -H "Authorization: Bearer $TOKEN"
```

Toggle tracking active flag (explicit):

```bash
curl -s -X PATCH "$BASE_URL/api/tracking/1/active" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active":false}'
```

Get tracking list:

```bash
curl -s "$BASE_URL/api/tracking" \
  -H "Authorization: Bearer $TOKEN"
```

Set target price for one tracking entry:

```bash
curl -s -X PATCH "$BASE_URL/api/tracking/1/target-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_price":39.99}'
```

Toggle tracking active flag (auto toggle):

```bash
curl -s -X PATCH "$BASE_URL/api/tracking/1/active" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Delete tracking entry:

```bash
curl -s -X DELETE "$BASE_URL/api/tracking/1" \
  -H "Authorization: Bearer $TOKEN"
```

## 3) Scraping Endpoint Quick Checks

URL scraping + persist product/tracking (protected endpoint):

```bash
curl -s -X POST "$BASE_URL/api/scrape/url" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.alternate.de/...product-url...","target_price":450.0}'
```

Category scraping (uses `name` as query and returns candidate list):

```bash
curl -s -X POST "$BASE_URL/api/scrape/category" \
  -H "Content-Type: application/json" \
  -d '{"category":"games","name":"elden ring","limit":10}'
```

## 4) Notes

- Protected routes always need a bearer token.
- In Swagger, first login via `/api/auth/login`, then paste `access_token` in Authorize.
- If your local user id is `1`, you still authenticate by email/password, not directly by id.
