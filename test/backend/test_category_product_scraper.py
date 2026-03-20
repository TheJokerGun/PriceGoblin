import unittest
from unittest.mock import patch

from src.backend.scrapers.category_product_scraper import CATEGORY_PROVIDERS, CategoryScraper


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


class CategoryProductScraperTests(unittest.TestCase):
    @patch("src.backend.scrapers.category_product_scraper.requests.get")
    def test_keyforsteam_provider_uses_comparison_page_url(self, get_mock) -> None:
        search_html = """
        <html>
          <body>
            <a href="https://www.keyforsteam.de/balatro-key-kaufen-preisvergleich/">Balatro Key kaufen Preisvergleich</a>
          </body>
        </html>
        """
        game_html = """
        <html>
          <head>
            <meta property="og:title" content="Balatro Key kaufen Preisvergleich" />
            <meta property="og:image" content="https://www.keyforsteam.de/wp-content/uploads/keyforsteamBalatro.jpg" />
          </head>
          <body>
            <a class="recomended_offers" href="https://www.allkeyshop.com/redirection/offer/eur/111?merchant=1">
              <span class="offers-merchant-name">G2A</span>
              <span class="offers-price">€ 11,49</span>
            </a>
            <a class="recomended_offers" href="https://www.allkeyshop.com/redirection/offer/eur/222?merchant=2">
              <span class="offers-merchant-name">Instant Gaming</span>
              <span class="offers-price">€ 9,99</span>
            </a>
          </body>
        </html>
        """
        get_mock.side_effect = [_FakeResponse(search_html), _FakeResponse(game_html)]

        scraper = CategoryScraper(locale="de-DE")
        provider = next(p for p in CATEGORY_PROVIDERS["games"] if p.name == "keyforsteam")

        results = scraper._scrape_keyforsteam_provider(provider, "balatro")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["price"], 9.99)
        self.assertEqual(results[0]["source"], "Instant Gaming")
        self.assertEqual(
            results[0]["url"],
            "https://www.keyforsteam.de/balatro-key-kaufen-preisvergleich/",
        )


if __name__ == "__main__":
    unittest.main()
