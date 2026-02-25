# scrapers/category_scraper.py

from playwright.sync_api import sync_playwright


class CategoryScraper:

    def scrape(self, category: str) -> list[dict]:
        """
        Main entry point.
        Decides which category logic to use.
        """

        category = category.lower()

        if category == "cards":
            return self._scrape_cards()

        elif category == "games":
            return self._scrape_games()

        else:
            return self._scrape_general(category)


    def _scrape_cards(self) -> list[dict]:
        """
        Scrapes trading card category pages.
        Returns list of products.
        """

        url = "https://example.com/cards"

        return self._scrape_category_page(url)


    def _scrape_games(self) -> list[dict]:
        """
        Scrapes games category.
        """

        url = "https://example.com/games"

        return self._scrape_category_page(url)


    def _scrape_general(self, category: str) -> list[dict]:
        """
        Fallback category scraping.
        """

        url = f"https://example.com/{category}"

        return self._scrape_category_page(url)


    def _scrape_category_page(self, url: str) -> list[dict]:
        """
        Generic category page scraping logic.
        """

        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            product_elements = page.locator(".product-card")

            count = product_elements.count()

            for i in range(count):
                element = product_elements.nth(i)

                name = element.locator(".product-title").inner_text()
                price_text = element.locator(".product-price").inner_text()

                products.append({
                    "name": name,
                    "price": price_text,
                })

            browser.close()

        return products
