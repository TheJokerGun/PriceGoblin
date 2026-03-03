import logging
from dataclasses import dataclass
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from ..logging_utils import configure_logging, format_exception_detail, log_event

logger = configure_logging()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    search_url_template: str
    item_selector: str
    title_selector: str
    price_selector: str


CATEGORY_PROVIDERS: dict[str, list[ProviderConfig]] = {
    "general": [
        ProviderConfig(
            name="idealo",
            search_url_template="https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={query}",
            item_selector=".offerList-item, .sr-resultItem, article, .result",
            title_selector=".offerList-item-description-title, .sr-resultItem__title, h2, h3, a",
            price_selector=".offerList-item-price, .sr-detailedPriceInfo__price, .price, [itemprop='price']",
        ),
        ProviderConfig(
            name="geizhals",
            search_url_template="https://geizhals.de/?fs={query}",
            item_selector=".row.productlist__product, .gh-list__item, article, .result",
            title_selector=".productlist__link, .gh-list__title, h2, h3, a",
            price_selector=".gh_price, .productlist__price, .price, [itemprop='price']",
        ),
    ],
    "steam": [
        ProviderConfig(
            name="steam",
            search_url_template="https://store.steampowered.com/search/?term={query}",
            item_selector="a.search_result_row, .search_result_row",
            title_selector=".title, span.title",
            price_selector=".search_price, .discount_final_price, .discount_original_price",
        ),
        ProviderConfig(
            name="steamkeys",
            search_url_template="https://www.steamkeys.com/?s={query}&post_type=product",
            item_selector=".product, li.product, article, .item",
            title_selector="h2, .woocommerce-loop-product__title, .title, a",
            price_selector=".price, .amount, [itemprop='price']",
        ),
    ],
    "cards": [
        ProviderConfig(
            name="cardmarket-pokemon",
            search_url_template="https://www.cardmarket.com/en/Pokemon/Products/Singles?searchString={query}",
            item_selector=".table-body .row, .product-row, article, .result",
            title_selector=".col-product a, .product-name, h2, h3, a",
            price_selector=".col-price, .price-container, .price, [itemprop='price']",
        ),
        ProviderConfig(
            name="cardmarket-yugioh",
            search_url_template="https://www.cardmarket.com/en/YuGiOh/Products/Singles?searchString={query}",
            item_selector=".table-body .row, .product-row, article, .result",
            title_selector=".col-product a, .product-name, h2, h3, a",
            price_selector=".col-price, .price-container, .price, [itemprop='price']",
        ),
    ],
}


class CategoryScraper:
    def scrape(self, category: str, query: str | None = None) -> list[dict]:
        category = category.lower().strip()
        query = (query or "").strip()

        log_event(
            logger,
            logging.INFO,
            "scrape.category.started",
            category=category,
            query=query or None,
        )

        providers = CATEGORY_PROVIDERS.get(category)
        if not providers:
            log_event(
                logger,
                logging.WARNING,
                "scrape.category.unsupported",
                category=category,
                supported=list(CATEGORY_PROVIDERS.keys()),
            )
            return []

        if not query:
            # Structure-first behavior: category exists but no concrete search term yet.
            return [
                {
                    "name": f"{category} search requires a query",
                    "price": None,
                    "source": provider.name,
                    "url": provider.search_url_template.format(query="<query>"),
                }
                for provider in providers
            ]

        all_results: list[dict] = []
        for provider in providers:
            provider_results = self._scrape_provider(provider, query)
            all_results.extend(provider_results)

        log_event(
            logger,
            logging.INFO,
            "scrape.category.completed",
            category=category,
            query=query,
            count=len(all_results),
        )
        return all_results

    def _scrape_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        target_url = provider.search_url_template.format(query=quote_plus(query))
        products: list[dict] = []

        try:
            response = requests.get(target_url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                log_event(
                    logger,
                    logging.WARNING,
                    "scrape.category.provider.non_200",
                    provider=provider.name,
                    url=target_url,
                    status_code=response.status_code,
                )
                return []

            soup = BeautifulSoup(response.text, "lxml")
            rows = soup.select(provider.item_selector)
            if not rows:
                log_event(
                    logger,
                    logging.INFO,
                    "scrape.category.provider.no_results",
                    provider=provider.name,
                    url=target_url,
                )
                return []

            for row in rows[:10]:
                title_node = row.select_one(provider.title_selector)
                if not title_node:
                    continue

                raw_name = title_node.get_text(" ", strip=True)
                if not raw_name:
                    continue

                price_node = row.select_one(provider.price_selector)
                raw_price = price_node.get_text(" ", strip=True) if price_node else None

                link = title_node.get("href") if hasattr(title_node, "get") else None
                if link and link.startswith("/"):
                    link = f"https://{target_url.split('/')[2]}{link}"

                products.append(
                    {
                        "name": raw_name,
                        "price": raw_price,
                        "source": provider.name,
                        "url": link or target_url,
                    }
                )

            return products
        except Exception as exc:
            log_event(
                logger,
                logging.WARNING,
                "scrape.category.provider.failed",
                provider=provider.name,
                url=target_url,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            return []
