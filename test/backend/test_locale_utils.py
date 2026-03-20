import unittest

from src.backend import locale_utils


class LocaleUtilsTests(unittest.TestCase):
    def test_normalize_locale_handles_case_and_underscore(self) -> None:
        self.assertEqual(locale_utils.normalize_locale("DE_de"), "de-DE")
        self.assertEqual(locale_utils.normalize_locale("en-us"), "en-US")

    def test_resolve_locale_uses_default(self) -> None:
        self.assertEqual(locale_utils.resolve_locale(None), locale_utils.DEFAULT_LOCALE)

    def test_build_accept_language_for_non_default_locale(self) -> None:
        value = locale_utils.build_accept_language("en-US")
        self.assertEqual(value, "en-US,en;q=0.9,en-US;q=0.8,en;q=0.7")

    def test_locale_region_extracts_region(self) -> None:
        self.assertEqual(locale_utils.locale_region("de-DE"), "DE")
        self.assertEqual(locale_utils.locale_region("en"), None)


if __name__ == "__main__":
    unittest.main()
