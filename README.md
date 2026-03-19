# PriceGoblin
Price Goblin is a unified price-watching and deal-tracking project that aggregates prices from multiple marketplaces and platforms—tech hardware, games, trading cards, and digital keys—into a single interface.

## Project Docs
- API contract: `docs/API_CONTRACT_OVERVIEW.md`
- Next work checklist: `docs/TODO_NEXT_STEPS.md`
- Endpoint testing guide: `docs/ENDPOINT_TESTING.md`
- Backend automated tests + protocol logging: `docs/BACKEND_AUTOMATED_TESTING.md`
- User manual: `docs/USER_MANUAL.md`

## Scraper Debugging
Use this when validating selectors against a new website or troubleshooting scraper failures.

```bash
uv run python scripts/debug_scrape.py "https://www.alternate.de/AMD/Ryzen-Threadripper-9960X-Prozessor/html/product/100145427"
```

Useful options:

```bash
# Run headless
uv run python scripts/debug_scrape.py "<url>" --headless

# Add custom selectors during experiments
uv run python scripts/debug_scrape.py "<url>" --price-selector ".my-price" --title-selector "h1.product-title"
```

Artifacts are written to `tmp/scrape_debug/<timestamp>/`:
- `report.json` (status, selector hits, parsed price)
- `page.png` (what Playwright rendered)
- `page.html` (post-render HTML)

## Category Scraper Debugging
Use this to compare provider quality for one category + query and pick primary/fallback providers.

```bash
uv run python scripts/debug_category_scrape.py general "ryzen 7 7800x3d"
```

Provider filter:

```bash
uv run python scripts/debug_category_scrape.py cards "charizard" --provider cardmarket-pokemon
```

Artifacts are written to `tmp/category_debug/<timestamp>/report.json` and include:
- result count per provider
- numeric-price parse rate per provider
- cheapest parsed price per provider
- recommended provider order (best first)
