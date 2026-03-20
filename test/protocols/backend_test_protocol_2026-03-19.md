# Backend Test Protocol

- Generated: 2026-03-19 08:12:40 UTC
- Commit: `9b4f3f6`
- Command: `/Users/noahw/repos/PriceGoblin/.venv/bin/python3 -m unittest discover -s test -p test_*.py -v`
- Exit Code: `0`

## Stdout
```text
<no stdout>
```

## Stderr
```text
test_build_accept_language_for_non_default_locale (backend.test_locale_utils.LocaleUtilsTests.test_build_accept_language_for_non_default_locale) ... ok
test_locale_region_extracts_region (backend.test_locale_utils.LocaleUtilsTests.test_locale_region_extracts_region) ... ok
test_normalize_locale_handles_case_and_underscore (backend.test_locale_utils.LocaleUtilsTests.test_normalize_locale_handles_case_and_underscore) ... ok
test_resolve_locale_uses_default (backend.test_locale_utils.LocaleUtilsTests.test_resolve_locale_uses_default) ... ok
test_maybe_notify_price_drop_creates_email_log (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_creates_email_log) ... 2026-03-19T09:12:40+0100 INFO pricegoblin.api {"event": "notification.email.sent", "tracking_id": 1, "price": 95.0, "target_price": 100.0}
ok
test_maybe_notify_price_drop_respects_cooldown (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_respects_cooldown) ... 2026-03-19T09:12:40+0100 INFO pricegoblin.api {"event": "notification.email.skipped", "tracking_id": 1, "price": 95.0, "target_price": 100.0}
ok
test_maybe_notify_price_drop_skips_when_price_above_target (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_skips_when_price_above_target) ... ok
test_extract_price_value_detects_free (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_detects_free) ... ok
test_extract_price_value_parses_german_decimal (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_parses_german_decimal) ... ok
test_extract_price_value_parses_us_decimal (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_parses_us_decimal) ... ok
test_extract_price_value_uses_integer_fallback (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_uses_integer_fallback) ... ok
test_is_free_price_text_ignores_shipping_context (backend.test_price_utils.PriceUtilsTests.test_is_free_price_text_ignores_shipping_context) ... ok
test_normalize_price_label_returns_free_label (backend.test_price_utils.PriceUtilsTests.test_normalize_price_label_returns_free_label) ... ok
test_bulk_category_selection_reuses_product_and_single_seed_price (backend.test_product_service.ProductServiceTests.test_bulk_category_selection_reuses_product_and_single_seed_price) ... ok
test_check_product_price_uses_fallback_when_scrape_missing (backend.test_product_service.ProductServiceTests.test_check_product_price_uses_fallback_when_scrape_missing) ... ok
test_create_product_without_url_creates_tracking (backend.test_product_service.ProductServiceTests.test_create_product_without_url_creates_tracking) ... ok
test_delete_product_keeps_shared_product_until_last_tracking_removed (backend.test_product_service.ProductServiceTests.test_delete_product_keeps_shared_product_until_last_tracking_removed) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.042s

OK
```

