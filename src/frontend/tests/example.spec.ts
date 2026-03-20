/// <reference types="node" />
import { test, expect, type Page } from '@playwright/test';

// ──────────────────────────────────────────────
// Mock data
// ──────────────────────────────────────────────
const MOCK_TOKEN = 'mock-jwt-token';

const MOCK_PRODUCTS = [
  {
    id: 1,
    name: 'Test Product 1',
    url: 'https://example.com/p1',
    image_url: null,
    source: 'amazon',
    created_at: new Date().toISOString(),
  },
];

const MOCK_TRACKINGS = [
  { id: 1, product_id: 1, is_active: true, target_price: null },
];

const MOCK_PRICES = [
  { id: 1, price: '50.00', checked_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 2, price: '45.00', checked_at: new Date().toISOString() },
];

const MOCK_SCRAPE_URL_RESULT = {
  name: 'New Scraped Product',
  url: 'https://example.com/new',
  price: 99.99,
  image_url: null,
  source: 'amazon',
};

const MOCK_SCRAPE_CATEGORY_RESULT = {
  data: [
    { name: 'Category Candidate 1', url: 'https://example.com/c1', price: 10.0, image_url: null, source: 'ebay' },
    { name: 'Category Candidate 2', url: 'https://example.com/c2', price: 20.0, image_url: null, source: 'ebay' },
  ],
};

// ──────────────────────────────────────────────
// Helper: set auth token & mock base API
// ──────────────────────────────────────────────
async function setupAuthenticatedSession(page: Page) {
  // Inject token before app boots so AuthContext reads it from localStorage
  await page.addInitScript((token) => {
    localStorage.setItem('token', token);
  }, MOCK_TOKEN);

  // Mock the dashboard data requests
  await page.route('**/api/products', (route) => route.fulfill({ json: MOCK_PRODUCTS }));
  await page.route('**/api/tracking', (route) => route.fulfill({ json: MOCK_TRACKINGS }));
  await page.route('**/api/products/*/current-price', (route) =>
    route.fulfill({ json: { price: 45.0 } }),
  );
}

// ──────────────────────────────────────────────
// Authentication Flows
// ──────────────────────────────────────────────
test.describe('Authentication Flows', () => {
  test('should allow a new user to register', async ({ page }) => {
    await page.route('**/api/auth/register', (route) =>
      route.fulfill({ json: { access_token: MOCK_TOKEN, token_type: 'bearer' } }),
    );
    await page.route('**/api/products', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/tracking', (route) => route.fulfill({ json: [] }));

    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'PriceGoblin' })).toBeVisible();

    // Switch to Register tab
    await page.getByRole('button', { name: 'Join' }).click();

    await page.getByPlaceholder('name@company.com').fill('newuser@test.com');
    await page.getByPlaceholder('••••••••').fill('securepassword');

    await page.getByRole('button', { name: 'Create Account' }).click();

    // Post-login: redirected to /home and Dashboard loads
    await expect(page).toHaveURL(/.*\/home/);
    await expect(page.getByText('The Hunt Begins')).toBeVisible();
  });

  test('should allow an existing user to log in', async ({ page }) => {
    await page.route('**/api/auth/login', (route) =>
      route.fulfill({ json: { access_token: MOCK_TOKEN, token_type: 'bearer' } }),
    );
    await page.route('**/api/products', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/tracking', (route) => route.fulfill({ json: [] }));

    await page.goto('/login');

    // Sign In tab is shown by default
    await page.getByPlaceholder('name@company.com').fill('existing@test.com');
    await page.getByPlaceholder('••••••••').fill('password123');

    await page.getByRole('button', { name: 'Access Watchlist' }).click();

    await expect(page).toHaveURL(/.*\/home/);
    await expect(page.getByText('The Hunt Begins')).toBeVisible();
  });
});

// ──────────────────────────────────────────────
// Authenticated User Flows
// ──────────────────────────────────────────────
test.describe('Authenticated User Flows', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
  });

  // ── Dashboard ──
  test('should display tracked products on the dashboard', async ({ page }) => {
    await page.goto('/home');
    await expect(page.getByTitle('Test Product 1')).toBeVisible();
  });

  // ── Track via URL ──
  test('should track a product by pasting its URL', async ({ page }) => {
    // Intercept the scrape call and return a resolved product
    const scrapeRequest = page.waitForRequest('**/api/scrape/url');
    await page.route('**/api/scrape/url', (route) =>
      route.fulfill({ json: MOCK_SCRAPE_URL_RESULT }),
    );

    await page.goto('/home');

    const input = page.getByPlaceholder('Enter URL or product name...');
    await input.fill('https://example.com/new');

    await page.getByRole('button', { name: 'Track Product' }).click();

    // Confirm the scrape request was made
    await scrapeRequest;

    // After success the input should be cleared back to empty
    await expect(input).toHaveValue('');
  });

  // ── Search category & add candidates ──
  test('should search by category name and add a candidate to tracking', async ({ page }) => {
    await page.route('**/api/scrape/category', (route) =>
      route.fulfill({ json: MOCK_SCRAPE_CATEGORY_RESULT }),
    );
    await page.route('**/api/products/bulk', (route) =>
      route.fulfill({ status: 201, json: {} }),
    );

    await page.goto('/home');

    // Select a category from the dropdown
    await page.locator('select').selectOption('general');

    const input = page.getByPlaceholder('Enter URL or product name...');
    await input.fill('headphones');

    await page.getByRole('button', { name: 'Track Product' }).click();

    // CandidateSelection view appears
    await expect(page.getByText('Select Products to Track')).toBeVisible();
    await expect(page.getByText('Category Candidate 1')).toBeVisible();

    // Click the first candidate card to select it
    await page.getByText('Category Candidate 1').click();

    // Track button should now say "Track 1 Selected Items"
    await page.getByRole('button', { name: 'Track 1 Selected Items' }).click();

    // Should navigate back to home after tracking
    await expect(page).toHaveURL(/.*\/home/);
  });

  // ── Search cards category ──
  test('should search using the Cards category', async ({ page }) => {
    await page.route('**/api/scrape/category', (route) =>
      route.fulfill({ json: MOCK_SCRAPE_CATEGORY_RESULT }),
    );
    await page.route('**/api/products/bulk', (route) =>
      route.fulfill({ status: 201, json: {} }),
    );

    await page.goto('/home');

    await page.locator('select').selectOption('cards');

    const input = page.getByPlaceholder('Enter URL or product name...');
    await input.fill('charizard');
    await page.getByRole('button', { name: 'Track Product' }).click();

    await expect(page.getByText('Select Products to Track')).toBeVisible();
    await expect(page.getByText('Category Candidate 2')).toBeVisible();
  });

  // ── Delete a tracked product ──
  test('should delete a tracked product from the dashboard', async ({ page }) => {
    await page.route('**/api/tracking/1', (route) => route.fulfill({ status: 204 }));

    await page.goto('/home');

    // The product card delete button is only visible on hover
    const productCard = page.locator('[title="Test Product 1"]').locator('../..');
    await productCard.hover();

    page.on('dialog', (dialog) => dialog.accept());
    await productCard.getByTitle('Delete Tracking').click();

    // Product should be removed from the list
    await expect(page.getByTitle('Test Product 1')).not.toBeVisible();
  });

  // ── Price History graph updates on Refresh ──
  test('should show price history chart and update price when refreshed', async ({ page }) => {
    // Product page data
    await page.route('**/api/products/1', (route) =>
      route.fulfill({ json: MOCK_PRODUCTS[0] }),
    );
    await page.route('**/api/products/1/prices', (route) =>
      route.fulfill({ json: MOCK_PRICES }),
    );
    await page.route('**/api/tracking', (route) => route.fulfill({ json: MOCK_TRACKINGS }));

    await page.goto('/productinfo?id=1');

    // Chart should render
    await expect(page.locator('.recharts-wrapper')).toBeVisible();

    // Mock the check-price call and the subsequent re-fetch of prices
    const newPrice = { id: 3, price: '42.00', checked_at: new Date().toISOString() };
    await page.route('**/api/products/1/check-price', (route) =>
      route.fulfill({ json: { price: 42.0 } }),
    );
    await page.route('**/api/products/1/prices', (route) =>
      route.fulfill({ json: [...MOCK_PRICES, newPrice] }),
    );

    // The refresh button only has a title attribute (icon-only button)
    await page.getByTitle('Refresh Price').click();

    // The chart should re-render with new data – recharts wrapper still visible
    await expect(page.locator('.recharts-wrapper')).toBeVisible();
  });
});
