# Backend Test Protocol

- Generated: 2026-03-20 19:08:00 UTC
- Commit: `0e86e64`
- Command: `C:\repo\SchuleCode\PriceGoblin\.venv\Scripts\python.exe -m unittest discover -s test -p test_*.py -v`
- Exit Code: `0`

## Stdout
```text
<no stdout>
```

## Stderr
```text
test_keyforsteam_provider_uses_comparison_page_url (backend.test_category_product_scraper.CategoryProductScraperTests.test_keyforsteam_provider_uses_comparison_page_url) ... 2026-03-20T20:08:01+0100 INFO pricegoblin.api {"event": "scrape.category.provider.success", "provider": "keyforsteam", "url": "https://www.keyforsteam.de/?s=balatro&post_type=product", "row_count": 1, "result_count": 1, "numeric_price_count": 1, "min_price": 9.99}
ok
test_build_accept_language_for_non_default_locale (backend.test_locale_utils.LocaleUtilsTests.test_build_accept_language_for_non_default_locale) ... ok
test_locale_region_extracts_region (backend.test_locale_utils.LocaleUtilsTests.test_locale_region_extracts_region) ... ok
test_normalize_locale_handles_case_and_underscore (backend.test_locale_utils.LocaleUtilsTests.test_normalize_locale_handles_case_and_underscore) ... ok
test_resolve_locale_uses_default (backend.test_locale_utils.LocaleUtilsTests.test_resolve_locale_uses_default) ... ok
test_maybe_notify_price_drop_creates_email_log (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_creates_email_log) ... 2026-03-20T20:08:01+0100 INFO pricegoblin.api {"event": "notification.email.sent", "tracking_id": 1, "price": 95.0, "target_price": 100.0}
ok
test_maybe_notify_price_drop_respects_cooldown (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_respects_cooldown) ... 2026-03-20T20:08:01+0100 INFO pricegoblin.api {"event": "notification.email.skipped", "tracking_id": 1, "price": 95.0, "target_price": 100.0}
ok
test_maybe_notify_price_drop_skips_when_price_above_target (backend.test_notification_service.NotificationServiceTests.test_maybe_notify_price_drop_skips_when_price_above_target) ... ok
test_extract_price_value_detects_free (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_detects_free) ... ok
test_extract_price_value_parses_german_decimal (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_parses_german_decimal) ... ok
test_extract_price_value_parses_single_decimal_digit (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_parses_single_decimal_digit) ... ok
test_extract_price_value_parses_us_decimal (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_parses_us_decimal) ... ok
test_extract_price_value_uses_integer_fallback (backend.test_price_utils.PriceUtilsTests.test_extract_price_value_uses_integer_fallback) ... ok
test_is_free_price_text_ignores_shipping_context (backend.test_price_utils.PriceUtilsTests.test_is_free_price_text_ignores_shipping_context) ... ok
test_normalize_price_label_returns_free_label (backend.test_price_utils.PriceUtilsTests.test_normalize_price_label_returns_free_label) ... ok
test_bulk_category_selection_reuses_product_and_single_seed_price (backend.test_product_service.ProductServiceTests.test_bulk_category_selection_reuses_product_and_single_seed_price) ... ok
test_check_product_price_returns_none_when_no_scrape_and_no_history (backend.test_product_service.ProductServiceTests.test_check_product_price_returns_none_when_no_scrape_and_no_history) ... 2026-03-20T20:08:01+0100 WARNING pricegoblin.api {"event": "product.check_price.scrape_missing_no_history", "product_id": 1, "url": null}
ok
test_check_product_price_reuses_latest_when_scrape_missing (backend.test_product_service.ProductServiceTests.test_check_product_price_reuses_latest_when_scrape_missing) ... 2026-03-20T20:08:01+0100 INFO pricegoblin.api {"event": "product.check_price.scrape_missing_using_latest", "product_id": 1, "url": null, "latest_price": 42.42}
ok
test_create_product_without_url_creates_tracking (backend.test_product_service.ProductServiceTests.test_create_product_without_url_creates_tracking) ... ok
test_delete_product_keeps_shared_product_until_last_tracking_removed (backend.test_product_service.ProductServiceTests.test_delete_product_keeps_shared_product_until_last_tracking_removed) ... ok
test_alternate_price_selectors_prefer_main_price_block (backend.test_url_product_scraper.UrlProductScraperTests.test_alternate_price_selectors_prefer_main_price_block) ... ok
test_json_ld_offer_price_with_single_decimal_digit (backend.test_url_product_scraper.UrlProductScraperTests.test_json_ld_offer_price_with_single_decimal_digit) ... ok

----------------------------------------------------------------------
Ran 22 tests in 0.084s

OK
```

