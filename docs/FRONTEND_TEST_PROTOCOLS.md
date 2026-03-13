# Frontend Test Protocols

This document outlines the testing protocols for the PriceGoblin frontend application using [Playwright](https://playwright.dev/).

## Purpose
The purpose of these end-to-end (E2E) integration tests is to ensure that key user flows and UI components function correctly within a real browser environment. This acts as a quality gate before deploying new features or bug fixes.

## Mock Strategy
All tests use Playwright's `page.route()` to intercept and mock HTTP requests to the backend API. This keeps the suite fast, deterministic, and independent of the live backend, database, or scraping services. No real network calls are made during test execution.

Authenticated tests inject a dummy JWT into `localStorage` (`token` key) via `addInitScript()` before the app boots, bypassing the login redirect.

## Test Coverage

All tests are located in `src/frontend/tests/example.spec.ts`.

### Authentication Flows
| Test | Description |
|------|-------------|
| `should allow a new user to register` | Mocks `POST /api/auth/register`, clicks the **Join** tab, fills in credentials, submits, and asserts redirect to `/home`. |
| `should allow an existing user to log in` | Mocks `POST /api/auth/login`, fills in the default **Sign In** form, submits, and assert redirect to `/home`. |

### Authenticated User Flows
All tests in this group pre-inject a mock token and mock `GET /products`, `GET /tracking`, and `GET /products/*/current-price` before each test.

| Test | Description |
|------|-------------|
| `should display tracked products on the dashboard` | Navigates to `/home` and asserts the mocked product name is visible. |
| `should track a product by pasting its URL` | Enters an Amazon-style URL, clicks **Track Product**, waits for the mocked `POST /api/scrape/url` request, and asserts the input is cleared on success. |
| `should search by category name and add a candidate to tracking` | Types a search term, clicks **Track Product** (triggering `POST /api/scrape/category`), selects a candidate from the selection view, clicks **Track 1 Selected Items**, and asserts return to `/home`. |
| `should search using the Cards category` | Same flow as above using the **Cards** category dropdown option. |
| `should delete a tracked product from the dashboard` | Hovers the product card, clicks the **Delete Tracking** icon button (title attribute), auto-accepts the confirm dialog, and asserts the product is removed from the DOM. |
| `should show price history chart and update price when refreshed` | Navigates to `/productinfo?id=1`, asserts the Recharts wrapper is visible, mocks `POST /api/products/1/check-price` with a new price, clicks the **Refresh Price** icon button (title attribute), and asserts the chart re-renders. |

## Browser Configuration

Tests currently run on **Chromium only**. Firefox and WebKit are commented out in `playwright.config.ts` and can be enabled after installing their binaries:

```bash
npx playwright install firefox webkit
```

Then uncomment the relevant project entries in `playwright.config.ts`.

## Running Tests

### Locally
1. Ensure the dev server is available (tests auto-start it via `npm run dev`):
   ```bash
   npm run test:e2e
   ```
2. For interactive debugging with the Playwright UI:
   ```bash
   npm run test:e2e:ui
   ```

### CI/CD Pipeline
The CI environment must install Playwright's Chromium binary before running tests:
```bash
npx playwright install --with-deps chromium
npm run test:e2e
```

## Writing Tests
- All test files go inside `src/frontend/tests/` and must end with `.spec.ts`.
- Use `page.route()` to mock API calls — do **not** depend on a live backend.
- Use `context.addInitScript()` to pre-set `localStorage` for authenticated flows.
- Prefer `getByRole()`, `getByPlaceholder()`, and `getByTitle()` over CSS selectors.
- Tests must be isolated and must not share mutable state across test cases.
