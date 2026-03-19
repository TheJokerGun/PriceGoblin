import unittest

from src.backend import price_utils


class PriceUtilsTests(unittest.TestCase):
    def test_extract_price_value_parses_german_decimal(self) -> None:
        self.assertEqual(price_utils.extract_price_value("1.234,56 EUR"), 1234.56)

    def test_extract_price_value_parses_us_decimal(self) -> None:
        self.assertEqual(price_utils.extract_price_value("$1,234.56"), 1234.56)

    def test_extract_price_value_uses_integer_fallback(self) -> None:
        self.assertEqual(price_utils.extract_price_value("1234"), 1234.0)

    def test_extract_price_value_detects_free(self) -> None:
        self.assertEqual(price_utils.extract_price_value("Free to play"), 0.0)

    def test_is_free_price_text_ignores_shipping_context(self) -> None:
        self.assertFalse(price_utils.is_free_price_text("Free shipping"))

    def test_normalize_price_label_returns_free_label(self) -> None:
        self.assertEqual(price_utils.normalize_price_label("gratis"), "Free")


if __name__ == "__main__":
    unittest.main()
