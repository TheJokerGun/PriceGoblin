import unittest

from bs4 import BeautifulSoup

from src.backend.scrapers import url_product_scraper


class UrlProductScraperTests(unittest.TestCase):
    def test_alternate_price_selectors_prefer_main_price_block(self) -> None:
        html = """
        <div>
          <span class="badge bg-red">
            <span class="d-flex">
              <span class="text-right font-weight-lighter">
                <span class="price">€ 294,00</span>
              </span>
            </span>
          </span>
          <div class="col campaign-timer-price-section">
            <div class="row align-items-baseline text-center text-md-left">
              <div class="col-12 col-md-auto">
                <span class="price">€ 679,00</span>
              </div>
            </div>
          </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = (
            url_product_scraper.SITE_CONFIGS["alternate"]["price_selectors"]
            + url_product_scraper.GENERIC_PRICE_SELECTORS
        )

        price = url_product_scraper._extract_price_from_soup(soup, selectors)

        self.assertEqual(price, 679.0)

    def test_json_ld_offer_price_with_single_decimal_digit(self) -> None:
        html = """
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Example Product",
          "offers": {
            "@type": "Offer",
            "priceCurrency": "EUR",
            "price": "679.0"
          }
        }
        </script>
        """
        soup = BeautifulSoup(html, "html.parser")

        _title, price, _image = url_product_scraper._extract_media_from_json_ld(
            soup, "https://example.com/product"
        )

        self.assertEqual(price, 679.0)


if __name__ == "__main__":
    unittest.main()
