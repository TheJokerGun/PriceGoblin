# Backend Automated Testing

This project includes backend-focused unit tests and a test protocol generator for school documentation.

## What Is Covered

- `test/backend/test_locale_utils.py`
  - Locale normalization and Accept-Language helpers.
- `test/backend/test_price_utils.py`
  - Price parsing and free-price normalization.
- `test/backend/test_product_service.py`
  - Product creation/tracking behavior, deduplication, deletion rules, fallback price checks.
- `test/backend/test_notification_service.py`
  - Notification trigger conditions, cooldown behavior, and notification log persistence.

## Run Tests (With Protocol Logging)

From the project root:

```bash
uv run python test/scripts/run_backend_tests.py
```

This command runs all backend unit tests and writes protocol reports to:

- `test/protocols/backend_test_protocol_latest.md`
- `test/protocols/backend_test_protocol_YYYY-MM-DD.md`

## Run Tests (Without Protocol File)

```bash
uv run python -m unittest discover -s test -p "test_*.py" -v
```
