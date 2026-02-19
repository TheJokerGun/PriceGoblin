# Development Guide: Price Tracker MVP

## 🛠 Tech Stack
- **Backend:** Python 3.12+ (managed by `uv`), FastAPI
- **Frontend:** React + TypeScript (Vite), Tailwind CSS
- **Database:** SQLite (SQLAlchemy/SQLModel)
- **Auth:** 

## 🏗 Architecture
1. **Scraping Strategy:**
2. **Database Schema:**
   - `User`: id, username, hashed_password
   - `Product`: id, name, target_url, current_price, last_updated, user_id
   - `PriceHistory`: id, product_id, price, timestamp

## 🚀 Setup
- **Backend Lib:** `uv add fastapi uvicorn sqlalchemy`
- **Frontend Lib:** `npm install axios react-router-dom`
- **Run Backend:** `uv run uvicorn app.main:app --reload`
- **Run Frontend:** `npm run dev`

## 🔐 API
- **Base URL:** `/api`
- **Authorization:** `{Authorization: Bearer <token>}`
- **Authentication:**
    - **endpoint:** POST `/api/auth/login`
    - **frontend sends:**`{"email": "student@school.de"}`
    - **backend returns:**`{"access_token": "jwt-token-string", "token_type": "bearer"}`
- **Products:**
    - **endpoint:** POST `/api/products`
    - **frontend sends:**
        - **URL tracking:** `{"name": "RTX 4070", "url": "https://example.com/product", "category": null}`
        - **Category tracking:** `{"name": "Pokemon Booster Box", "url": null, "category": "Cards"}`
    - **backend returns:** `{"id": 1, "name": "RTX 4070", "url": "https://example.com/product", "category": null, "created_at": "2026-02-18T12:00:00"}`
    - **endpoint:** GET `/api/products`
    - **backend returns:** `[{"id": 1, "name": "RTX 4070", "url": "https://example.com/product", "category": null, "created_at": "2026-02-18T12:00:00"}]
    - **endpoint:** GET `/api/products/{id}`
    - **backend returns:** `{"id": 1, "name": "RTX 4070", "url": "https://example.com/product", "category": null, "created_at": "2026-02-18T12:00:00"}`
    - **endpoint:** DELETE `/api/products/{id}`
    - **backend returns:** `{"message": "Product deleted successfully"}`
- **Prices:**
    - **endpoint:** GET `/api/products/{id}/prices`
    - **backend returns:** `[{"id": 10, "price": 499.99, "checked_at": "2026-02-18T12:00:00"}, {"id": 11, "price": 479.99, "checked_at": "2026-02-19T12:00:00"}]`
    - **endpoint:** POST `/api/products/{id}/check-price`
    - **backend returns:** `{"price": 489.99, "checked_at": "2026-02-20T12:00:00"}`
- **Agreements:**
    - **Frontend must:**
        - no missing fields, seand null insetead
        - include JWT token after login
        - handle 401 (unauthorized) properly
    - **Backend guarantees:**
        - all responses are consistent JSON
        - dates are ISO format
        - user only sees their own products
        - Proper HTTP status codes (200, 201, 401, 404)