import logging
import re
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, FeatureNotFound

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


def _extract_price_value(text: str | None) -> float | None:
    if not text:
        return None

    match = re.search(r"(\d{1,3}(?:[.\s]\d{3})*[.,]\d{2}|\d+[.,]\d{2})", text)
    if not match:
        return None
    normalized = match.group(1).replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) >= 2]


def _relevance_score(query: str, candidate: str) -> int:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return 1
    candidate_tokens = set(_tokenize(candidate))
    return len(query_tokens.intersection(candidate_tokens))


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
    "games": [
        ProviderConfig(
            name="steam",
            search_url_template="https://store.steampowered.com/search/?term={query}",
            item_selector="a.search_result_row, .search_result_row",
            title_selector=".title, span.title",
            price_selector=".search_price, .discount_final_price, .discount_original_price",
        ),
        ProviderConfig(
            name="keyforsteam",
            search_url_template="https://www.keyforsteam.de/?s={query}&post_type=product",
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
    @staticmethod
    def _build_soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except FeatureNotFound:
            # Fallback keeps scraping alive when optional lxml isn't installed.
            return BeautifulSoup(html, "html.parser")

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
        if provider.name == "keyforsteam":
            return self._scrape_keyforsteam_provider(provider, query)

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

            soup = self._build_soup(response.text)
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
                relevance = _relevance_score(query, raw_name)
                if relevance == 0:
                    continue

                price_node = row.select_one(provider.price_selector)
                raw_price = price_node.get_text(" ", strip=True) if price_node else None
                parsed_price = _extract_price_value(raw_price)

                link = title_node.get("href") if hasattr(title_node, "get") else None
                if not link and hasattr(row, "get"):
                    link = row.get("href")
                if not link:
                    anchor = row.select_one("a[href]")
                    link = anchor.get("href") if anchor else None
                if link:
                    link = urljoin(target_url, link)

                products.append(
                    {
                        "name": raw_name,
                        "price": parsed_price if parsed_price is not None else raw_price,
                        "source": provider.name,
                        "url": link or target_url,
                        "relevance_score": relevance,
                    }
                )

            prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
            products.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    item["price"] if isinstance(item.get("price"), (int, float)) else float("inf"),
                    item.get("name") or "",
                )
            )
            for item in products:
                item.pop("relevance_score", None)
            log_event(
                logger,
                logging.INFO,
                "scrape.category.provider.success",
                provider=provider.name,
                url=target_url,
                row_count=len(rows),
                result_count=len(products),
                numeric_price_count=len(prices),
                min_price=min(prices) if prices else None,
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

    def _scrape_keyforsteam_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        target_url = provider.search_url_template.format(query=quote_plus(query))

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

            soup = self._build_soup(response.text)
            link_nodes = soup.select(
                "a[href*='key-kaufen-preisvergleich'], "
                "a[href*='-preisvergleich/'], "
                "a[href*='/kaufe-']"
            )

            candidates: list[tuple[int, str]] = []
            seen: set[str] = set()
            for node in link_nodes:
                href = (node.get("href") or "").strip()
                if not href:
                    continue
                href = urljoin(target_url, href)
                parsed = urlparse(href)
                if "keyforsteam.de" not in parsed.netloc:
                    continue
                path = parsed.path.lower()
                if path.startswith("/page/"):
                    continue
                if "/review/" in path or "-news-" in path:
                    continue
                if "preisvergleich" not in path:
                    continue
                if href in seen:
                    continue
                seen.add(href)
                score = _relevance_score(query, f"{node.get_text(' ', strip=True)} {path}")
                if score <= 0:
                    continue
                candidates.append((score, href))

            candidates.sort(key=lambda item: (-item[0], item[1]))
            offers: list[dict] = []

            for score, game_url in candidates[:8]:
                game_resp = requests.get(game_url, headers=HEADERS, timeout=20)
                if game_resp.status_code != 200:
                    continue
                game_soup = self._build_soup(game_resp.text)

                game_title = None
                meta_title = game_soup.select_one("meta[property='og:title']")
                if meta_title and meta_title.get("content"):
                    game_title = meta_title.get("content").strip()
                if not game_title and game_soup.title:
                    game_title = game_soup.title.get_text(" ", strip=True)
                game_title = game_title or game_url

                page_offers: list[dict] = []
                for offer_node in game_soup.select("a.recomended_offers"):
                    merchant_node = offer_node.select_one(".offers-merchant-name")
                    merchant = merchant_node.get_text(" ", strip=True) if merchant_node else "unknown"
                    price_node = offer_node.select_one(".offers-price")
                    price_text = price_node.get_text(" ", strip=True) if price_node else None
                    price = _extract_price_value(price_text)
                    redirect_url = (offer_node.get("href") or "").strip() or game_url
                    if not redirect_url.startswith("http"):
                        redirect_url = urljoin(game_url, redirect_url)
                    if price is None:
                        continue
                    page_offers.append(
                        {
                            "name": game_title,
                            "price": price,
                            "source": merchant,
                            "url": redirect_url,
                            "relevance_score": score,
                        }
                    )

                if not page_offers:
                    continue

                page_offers.sort(key=lambda item: item["price"])
                offers.append(page_offers[0])

            offers.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    item["price"] if isinstance(item.get("price"), (int, float)) else float("inf"),
                    item.get("name") or "",
                )
            )
            for item in offers:
                item.pop("relevance_score", None)

            log_event(
                logger,
                logging.INFO,
                "scrape.category.provider.success",
                provider=provider.name,
                url=target_url,
                row_count=len(candidates),
                result_count=len(offers),
                numeric_price_count=len(offers),
                min_price=min([o["price"] for o in offers], default=None),
            )
            return offers
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
