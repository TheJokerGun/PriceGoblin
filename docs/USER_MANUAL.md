# PriceGoblin User Manual

Welcome to PriceGoblin. This guide explains how to use the website step by step, even if this is your first time.

## 1) What PriceGoblin Does

PriceGoblin helps you track product prices and monitor changes over time.

You can:
- Create an account and log in.
- Track a product directly from a product URL.
- Search by product name/category and select items to track.
- View tracked items in your dashboard.
- Open product details and see price history.
- Refresh prices manually.
- Pause/resume tracking.
- Set or remove a target price.
- Delete tracking entries.

## 2) What PriceGoblin Cannot Do (Current Scope)

- It does not guarantee scraping support for every website.
- It does not auto-check prices on a fixed schedule from the UI (refresh is manual in the app).
- Notifications only work if notification providers are configured by the system admin.
- If a source page blocks scraping or changes structure, price updates may fail until selectors are updated.

## 3) Getting Started

1. Open the website.
2. Register a new account or log in with an existing account.
3. After successful login, you are redirected to the dashboard.

Screenshot placeholder:
- `docs/screenshots/user-manual/01-login-page.png`

## 4) Dashboard Overview

On the dashboard, you can:
- Enter a product URL **or** a product name.
- Choose a category (`General`, `Cards`, `Game Keys`).
- Click **Track Product**.
- View active and paused tracked items.
- Refresh, pause/resume, or delete tracking from product cards.

Screenshot placeholder:
- `docs/screenshots/user-manual/02-dashboard-overview.png`

## 5) Two Ways to Track Products

### A) Track by Direct URL

1. Paste a valid product URL in the search field.
2. Click **Track Product**.
3. PriceGoblin will try to scrape product details and add the item to your dashboard.

Screenshot placeholder:
- `docs/screenshots/user-manual/03-track-by-url.png`

### B) Track by Name + Category (Candidate Selection)

1. Enter a product name (for example, `RTX 4070`) instead of a URL.
2. Choose the correct category.
3. Click **Track Product**.
4. PriceGoblin shows a candidate list.
5. Select one or more items.
6. Click **Track Selected Items**.

Screenshot placeholders:
- `docs/screenshots/user-manual/04-category-search-results.png`
- `docs/screenshots/user-manual/05-track-selected-items.png`

## 6) Product Card Actions (Dashboard)

Each tracked item card supports:
- **Refresh Price**: fetch current price now.
- **Pause/Resume**: disable or enable active monitoring state.
- **Delete**: remove tracking entry.
- **Open Details**: click card to open product detail page.

Screenshot placeholder:
- `docs/screenshots/user-manual/06-product-card-actions.png`

## 7) Product Detail Page

On the product details page you can:
- See product image, source link, and summary stats.
- See price chart/history.
- Refresh price.
- Pause/resume tracking.
- Delete tracking.
- Set, change, or remove a target price.

Screenshot placeholders:
- `docs/screenshots/user-manual/07-product-details-page.png`
- `docs/screenshots/user-manual/08-price-chart-and-target-price.png`

## 8) Target Price and Notifications

When you set a target price:
- PriceGoblin checks if a refreshed price is at or below your target.
- If notification channels are configured, alerts can be sent (for example email/Teams).
- Cooldown logic may prevent repeated alerts within a short period.

Screenshot placeholder:
- `docs/screenshots/user-manual/09-target-price-notification.png`

## 9) Troubleshooting

### "Login failed"
- Check email and password.
- Make sure your account is registered.

### "No products found"
- Try another search term.
- Switch category.
- Try a direct product URL.

### "Failed to refresh price"
- The source site may be temporarily unavailable.
- The source page structure may have changed.
- Try again later or re-add tracking with a cleaner URL.

## 10) Quick User Flow Summary

1. Log in.
2. Add products by URL or category search.
3. Monitor dashboard.
4. Open details for deeper price analysis.
5. Set target prices and react to alerts.

---

If you are preparing a report/submission, insert the screenshots in the placeholder file names listed above.
