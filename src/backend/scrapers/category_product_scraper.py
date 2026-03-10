import logging
import re
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, FeatureNotFound
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from ..logging_utils import configure_logging, format_exception_detail, log_event
from ..price_utils import extract_price_value, is_free_price_text

logger = configure_logging()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}

TCGPLAYER_SEARCH_API_URL = "https://mp-search-api.tcgplayer.com/v1/search/request"
CARDMARKET_GAMES = ("Pokemon", "Magic", "YuGiOh")
IDEALO_WEBKIT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
)


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    search_url_template: str
    item_selector: str
    title_selector: str
    price_selector: str


def _extract_price_value(text: str | None) -> float | None:
    return extract_price_value(text)


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) >= 2]


def _relevance_score(query: str, candidate: str) -> int:
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return 1
    candidate_tokens = set(_tokenize(candidate))
    return len(query_tokens.intersection(candidate_tokens))


ACCESSORY_KEYWORDS = {
    "case",
    "cover",
    "hulle",
    "hülle",
    "schutzglas",
    "schutzfolie",
    "folie",
    "cable",
    "kabel",
    "adapter",
    "halter",
    "mount",
    "rolle",
    "rollen",
    "caster",
    "gasfeder",
    "ersatz",
    "waterblock",
    "eisblock",
    "kuehler",
    "kühler",
    "cooler",
    "backplate",
}


MULTIPACK_KEYWORDS = {
    "pack",
    "packs",
    "set",
    "tray",
    "bundle",
    "karton",
    "case",
    "stueck",
    "stück",
    "pieces",
}

NON_CORE_KEYWORDS = {
    "komplettsystem",
    "system",
    "notebook",
    "laptop",
    "desktop",
    "workstation",
    "server",
    "mini",
    "pc",
}


def _keyword_penalty(query: str, candidate: str, keywords: set[str]) -> int:
    query_tokens = set(_tokenize(query))
    candidate_tokens = set(_tokenize(candidate))
    if not keywords.intersection(candidate_tokens):
        return 0
    # Do not penalize when user explicitly searches that subtype/accessory.
    return 0 if keywords.intersection(query_tokens) else 1


def _accessory_penalty(query: str, candidate: str) -> int:
    return _keyword_penalty(query, candidate, ACCESSORY_KEYWORDS)


def _multipack_penalty(query: str, candidate: str) -> int:
    candidate_lower = candidate.lower()
    query_lower = query.lower()

    has_multi = bool(re.search(r"\b\d+\s*[xX]\b", candidate_lower)) or bool(
        MULTIPACK_KEYWORDS.intersection(set(_tokenize(candidate)))
    )
    if not has_multi:
        return 0

    # If query explicitly asks for multipacks, keep those results.
    query_has_multi = bool(re.search(r"\b\d+\s*[xX]\b", query_lower)) or bool(
        MULTIPACK_KEYWORDS.intersection(set(_tokenize(query)))
    )
    return 0 if query_has_multi else 1


def _non_core_penalty(query: str, candidate: str) -> int:
    return _keyword_penalty(query, candidate, NON_CORE_KEYWORDS)


def _query_position(query: str, candidate: str) -> int:
    q = " ".join(query.lower().split())
    c = " ".join(candidate.lower().split())
    if not q:
        return 0
    idx = c.find(q)
    return idx if idx >= 0 else 9999


def _price_sort_value(value: str | float | int | None) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip().lower() == "free":
        return 0.0
    return float("inf")


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
            name="cardmarket",
            search_url_template="https://www.cardmarket.com/en/Pokemon/Products/Singles?searchString={query}",
            item_selector=".table-body .row, .product-row, article, .result",
            title_selector=".col-product a, .product-name, h2, h3, a",
            price_selector=".col-price, .price-container, .price, [itemprop='price']",
        ),
        ProviderConfig(
            name="tcgplayer",
            search_url_template="https://www.tcgplayer.com/search/all/product?q={query}&view=grid",
            item_selector=".search-result",
            title_selector=".product-card__title, h4, a",
            price_selector=".inventory__price-with-shipping, .product-card__market-price--value, .price",
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

        provider_buckets: list[list[dict]] = []
        for provider in providers:
            provider_results = self._scrape_provider(provider, query)
            provider_buckets.append(provider_results)

        # Keep provider diversity in the first page of candidates (important with endpoint limits).
        all_results: list[dict] = []
        max_bucket_len = max((len(bucket) for bucket in provider_buckets), default=0)
        for idx in range(max_bucket_len):
            for bucket in provider_buckets:
                if idx < len(bucket):
                    all_results.append(bucket[idx])

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
        if provider.name == "idealo":
            return self._scrape_idealo_provider(provider, query)
        if provider.name == "geizhals":
            return self._scrape_geizhals_provider(provider, query)
        if provider.name == "keyforsteam":
            return self._scrape_keyforsteam_provider(provider, query)
        if provider.name == "cardmarket":
            return self._scrape_cardmarket_provider(provider, query)
        if provider.name == "tcgplayer":
            return self._scrape_tcgplayer_provider(provider, query)

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
                normalized_price: str | float | None = parsed_price if parsed_price is not None else raw_price
                if is_free_price_text(raw_price):
                    normalized_price = "Free"

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
                        "price": normalized_price,
                        "source": provider.name,
                        "url": link or target_url,
                        "relevance_score": relevance,
                    }
                )

            prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
            products.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    _price_sort_value(item.get("price")),
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

    def _minimum_relevance(self, query: str) -> int:
        token_count = len(set(_tokenize(query)))
        return 1 if token_count <= 2 else 2

    def _scrape_idealo_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        target_url = provider.search_url_template.format(query=quote_plus(query))
        min_relevance = self._minimum_relevance(query)
        stage = "init"

        browser = None
        try:
            with sync_playwright() as p:
                stage = "browser_launch"
                browser = p.webkit.launch(headless=True)
                stage = "new_context"
                context = browser.new_context(
                    user_agent=IDEALO_WEBKIT_USER_AGENT,
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    viewport={"width": 1366, "height": 900},
                )
                page = context.new_page()
                page.set_extra_http_headers(
                    {
                        "Accept-Language": HEADERS["Accept-Language"],
                        "Referer": HEADERS["Referer"],
                    }
                )

                stage = "goto"
                response = page.goto(target_url, timeout=90000)
                if response and response.status >= 400:
                    log_event(
                        logger,
                        logging.WARNING,
                        "scrape.category.provider.non_200",
                        provider=provider.name,
                        url=target_url,
                        status_code=response.status,
                    )
                    return []

                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except PlaywrightTimeoutError:
                    pass
                page.wait_for_timeout(2500)

                if "sorry! something has gone wrong" in page.locator("body").inner_text().lower():
                    log_event(
                        logger,
                        logging.WARNING,
                        "scrape.category.provider.rate_limited",
                        provider=provider.name,
                        url=target_url,
                    )
                    return []

                rows = page.locator("[class*='sr-resultList__item']")
                row_count = rows.count()
                if row_count == 0:
                    log_event(
                        logger,
                        logging.INFO,
                        "scrape.category.provider.no_results",
                        provider=provider.name,
                        url=target_url,
                    )
                    return []

                products: list[dict] = []
                seen: set[str] = set()
                for idx in range(min(row_count, 60)):
                    row = rows.nth(idx)

                    title_loc = row.locator("[class*='sr-productSummary__title']")
                    if title_loc.count() == 0:
                        continue
                    raw_name = " ".join(title_loc.first.inner_text().split())
                    if not raw_name:
                        continue

                    relevance = _relevance_score(query, raw_name)
                    if relevance < min_relevance:
                        continue

                    price_loc = row.locator("[class*='sr-detailedPriceInfo__price']")
                    price_text = " ".join(price_loc.first.inner_text().split()) if price_loc.count() else None
                    parsed_price = _extract_price_value(price_text)
                    if parsed_price is None:
                        continue
                    normalized_price: str | float = "Free" if is_free_price_text(price_text) else parsed_price

                    link = None
                    link_loc = row.locator("[class*='sr-resultItemLink'] a[href]")
                    if link_loc.count() > 0:
                        link = link_loc.first.get_attribute("href")
                    if not link:
                        link_loc = row.locator("a[href*='/preisvergleich/OffersOfProduct/']")
                        if link_loc.count() > 0:
                            link = link_loc.first.get_attribute("href")
                    if not link:
                        link_loc = row.locator("a[href]")
                        if link_loc.count() > 0:
                            link = link_loc.first.get_attribute("href")
                    if link:
                        link = urljoin(page.url, link)
                    final_url = link or target_url
                    if final_url in seen:
                        continue
                    seen.add(final_url)

                    products.append(
                        {
                            "name": raw_name,
                            "price": normalized_price,
                            "source": provider.name,
                            "url": final_url,
                            "relevance_score": relevance,
                            "accessory_penalty": _accessory_penalty(query, raw_name),
                            "multipack_penalty": _multipack_penalty(query, raw_name),
                            "non_core_penalty": _non_core_penalty(query, raw_name),
                            "query_position": _query_position(query, raw_name),
                            "link_penalty": 1 if final_url == target_url else 0,
                        }
                    )

                prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
                products.sort(
                    key=lambda item: (
                        int(item.get("accessory_penalty", 0)),
                        int(item.get("multipack_penalty", 0)),
                        int(item.get("non_core_penalty", 0)),
                        -int(item.get("relevance_score", 0)),
                        int(item.get("query_position", 9999)),
                        int(item.get("link_penalty", 0)),
                        _price_sort_value(item.get("price")),
                        item.get("name") or "",
                    )
                )
                for item in products:
                    item.pop("relevance_score", None)
                    item.pop("accessory_penalty", None)
                    item.pop("multipack_penalty", None)
                    item.pop("non_core_penalty", None)
                    item.pop("query_position", None)
                    item.pop("link_penalty", None)

                log_event(
                    logger,
                    logging.INFO,
                    "scrape.category.provider.success",
                    provider=provider.name,
                    url=target_url,
                    row_count=row_count,
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
                stage=stage,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            return []
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

    def _scrape_geizhals_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        target_url = provider.search_url_template.format(query=quote_plus(query))
        min_relevance = self._minimum_relevance(query)
        stage = "init"

        browser = None
        try:
            with sync_playwright() as p:
                stage = "browser_launch"
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )
                stage = "new_context"
                context = browser.new_context(
                    user_agent=HEADERS["User-Agent"],
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    viewport={"width": 1366, "height": 900},
                )
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                page = context.new_page()
                page.set_extra_http_headers(
                    {
                        "Accept-Language": HEADERS["Accept-Language"],
                        "Referer": HEADERS["Referer"],
                    }
                )

                stage = "goto"
                response = page.goto(target_url, timeout=90000)
                if response and response.status >= 400:
                    log_event(
                        logger,
                        logging.WARNING,
                        "scrape.category.provider.non_200",
                        provider=provider.name,
                        url=target_url,
                        status_code=response.status,
                    )
                    return []

                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except PlaywrightTimeoutError:
                    pass
                page.wait_for_timeout(2000)

                rows = page.locator("article")
                row_count = rows.count()
                if row_count == 0:
                    log_event(
                        logger,
                        logging.INFO,
                        "scrape.category.provider.no_results",
                        provider=provider.name,
                        url=target_url,
                    )
                    return []

                products: list[dict] = []
                seen: set[str] = set()
                for idx in range(min(row_count, 60)):
                    row = rows.nth(idx)
                    title_loc = row.locator("h3 .galleryview__name-link")
                    if title_loc.count() == 0:
                        title_loc = row.locator("h3 a[href]")
                    if title_loc.count() == 0:
                        continue

                    raw_name = " ".join(title_loc.first.inner_text().split())
                    if not raw_name:
                        continue

                    relevance = _relevance_score(query, raw_name)
                    if relevance < min_relevance:
                        continue

                    price_loc = row.locator(".galleryview__price .price")
                    if price_loc.count() == 0:
                        price_loc = row.locator(".price")
                    price_text = " ".join(price_loc.first.inner_text().split()) if price_loc.count() else None
                    parsed_price = _extract_price_value(price_text)
                    if parsed_price is None:
                        continue
                    normalized_price: str | float = "Free" if is_free_price_text(price_text) else parsed_price

                    link = title_loc.first.get_attribute("href")
                    if link:
                        link = urljoin(page.url, link)
                    final_url = link or target_url
                    if final_url in seen:
                        continue
                    seen.add(final_url)

                    products.append(
                        {
                            "name": raw_name,
                            "price": normalized_price,
                            "source": provider.name,
                            "url": final_url,
                            "relevance_score": relevance,
                            "accessory_penalty": _accessory_penalty(query, raw_name),
                            "multipack_penalty": _multipack_penalty(query, raw_name),
                            "non_core_penalty": _non_core_penalty(query, raw_name),
                            "query_position": _query_position(query, raw_name),
                            "link_penalty": 1 if final_url == target_url else 0,
                        }
                    )

                prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
                products.sort(
                    key=lambda item: (
                        int(item.get("accessory_penalty", 0)),
                        int(item.get("multipack_penalty", 0)),
                        int(item.get("non_core_penalty", 0)),
                        -int(item.get("relevance_score", 0)),
                        int(item.get("query_position", 9999)),
                        int(item.get("link_penalty", 0)),
                        _price_sort_value(item.get("price")),
                        item.get("name") or "",
                    )
                )
                for item in products:
                    item.pop("relevance_score", None)
                    item.pop("accessory_penalty", None)
                    item.pop("multipack_penalty", None)
                    item.pop("non_core_penalty", None)
                    item.pop("query_position", None)
                    item.pop("link_penalty", None)

                log_event(
                    logger,
                    logging.INFO,
                    "scrape.category.provider.success",
                    provider=provider.name,
                    url=target_url,
                    row_count=row_count,
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
                stage=stage,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            return []
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

    def _scrape_tcgplayer_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        target_url = provider.search_url_template.format(query=quote_plus(query))
        request_url = f"{TCGPLAYER_SEARCH_API_URL}?q={quote_plus(query)}&isList=false"
        payload = {
            "algorithm": "sales_dismax",
            "from": 0,
            "size": 24,
            "filters": {"term": {}, "range": {}, "match": {}},
            "listingSearch": {
                "context": {"cart": {}},
                "filters": {
                    "term": {"sellerStatus": "Live", "channelId": 0},
                    "range": {"quantity": {"gte": 1}},
                    "exclude": {"channelExclusion": 0},
                },
            },
            "context": {"cart": {}, "shippingCountry": "DE", "userProfile": {}},
            "settings": {"useFuzzySearch": True, "didYouMean": {}},
            "sort": {},
        }
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://www.tcgplayer.com/",
            "Origin": "https://www.tcgplayer.com",
            "User-Agent": HEADERS["User-Agent"],
            "Accept-Language": HEADERS["Accept-Language"],
        }

        try:
            response = requests.post(request_url, json=payload, headers=headers, timeout=25)
            if response.status_code != 200:
                log_event(
                    logger,
                    logging.WARNING,
                    "scrape.category.provider.non_200",
                    provider=provider.name,
                    url=request_url,
                    status_code=response.status_code,
                )
                return []

            data = response.json()
            buckets = data.get("results") or []
            first_bucket = buckets[0] if buckets and isinstance(buckets[0], dict) else {}
            rows = first_bucket.get("results") or []
            if not rows:
                log_event(
                    logger,
                    logging.INFO,
                    "scrape.category.provider.no_results",
                    provider=provider.name,
                    url=request_url,
                )
                return []

            products: list[dict] = []
            for index, row in enumerate(rows[:24]):
                raw_name = (row.get("productName") or "").strip()
                if not raw_name:
                    continue
                relevance = _relevance_score(query, raw_name)
                if relevance == 0:
                    continue

                price = row.get("lowestPriceWithShipping")
                if not isinstance(price, (int, float)):
                    price = row.get("lowestPrice")
                if not isinstance(price, (int, float)):
                    price = row.get("marketPrice")
                if isinstance(price, str):
                    price = _extract_price_value(price)
                if not isinstance(price, (int, float)):
                    continue

                product_id = row.get("productId")
                item_url = target_url
                if isinstance(product_id, (int, float)):
                    item_url = f"https://www.tcgplayer.com/product/{int(product_id)}"

                score = row.get("score")
                if not isinstance(score, (int, float)):
                    score = 0.0

                products.append(
                    {
                        "name": raw_name,
                        "price": float(price),
                        "source": provider.name,
                        "url": item_url,
                        "relevance_score": relevance,
                        "api_score": float(score),
                        "provider_rank": index,
                    }
                )

            prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
            products.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    -float(item.get("api_score", 0.0)),
                    int(item.get("provider_rank", 999999)),
                    _price_sort_value(item.get("price")),
                    item.get("name") or "",
                )
            )
            for item in products:
                item.pop("relevance_score", None)
                item.pop("api_score", None)
                item.pop("provider_rank", None)

            log_event(
                logger,
                logging.INFO,
                "scrape.category.provider.success",
                provider=provider.name,
                url=request_url,
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
                url=request_url,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            return []

    def _scrape_cardmarket_provider(self, provider: ProviderConfig, query: str) -> list[dict]:
        products: list[dict] = []
        seen_urls: set[str] = set()
        row_count = 0
        source_url = provider.search_url_template.format(query=quote_plus(query))

        stage = "init"
        browser = None
        try:
            stage = "playwright_context"
            with sync_playwright() as p:
                stage = "browser_launch"
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )
                stage = "new_context"
                context = browser.new_context(
                    user_agent=HEADERS["User-Agent"],
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    viewport={"width": 1366, "height": 900},
                )
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                page = context.new_page()
                page.set_extra_http_headers(
                    {
                        "Accept-Language": HEADERS["Accept-Language"],
                        "Referer": HEADERS["Referer"],
                    }
                )

                for game in CARDMARKET_GAMES:
                    game_url = (
                        f"https://www.cardmarket.com/en/{game}/Products/Singles"
                        f"?searchString={quote_plus(query)}"
                    )
                    stage = f"goto:{game}"
                    response = page.goto(game_url, timeout=90000)
                    if response and response.status >= 400:
                        log_event(
                            logger,
                            logging.WARNING,
                            "scrape.category.provider.non_200",
                            provider=provider.name,
                            url=game_url,
                            status_code=response.status,
                        )
                        continue

                    try:
                        page.wait_for_load_state("networkidle", timeout=8000)
                    except PlaywrightTimeoutError:
                        pass

                    page.wait_for_timeout(2500)
                    page_title = page.title().strip().lower()
                    if "just a moment" in page_title:
                        log_event(
                            logger,
                            logging.WARNING,
                            "scrape.category.provider.rate_limited",
                            provider=provider.name,
                            url=game_url,
                        )
                        continue

                    cards = page.locator("a.galleryBox")
                    card_count = cards.count()
                    row_count += card_count
                    if card_count == 0:
                        continue

                    for idx in range(min(card_count, 12)):
                        card = cards.nth(idx)
                        href = (card.get_attribute("href") or "").strip()
                        if not href:
                            continue
                        item_url = urljoin(game_url, href)
                        if item_url in seen_urls:
                            continue

                        name = ""
                        if card.locator(".card-title").count() > 0:
                            name = card.locator(".card-title").first.inner_text().strip()
                        if not name:
                            name = card.inner_text().strip().split("\n")[0]
                        name = re.sub(r"\s+", " ", name).strip()
                        if not name:
                            continue

                        relevance = _relevance_score(query, name)
                        if relevance == 0:
                            continue

                        price_text = None
                        if card.locator(".card-text.text-muted b").count() > 0:
                            price_text = card.locator(".card-text.text-muted b").first.inner_text()
                        if not price_text and card.locator(".card-text.text-muted").count() > 0:
                            price_text = card.locator(".card-text.text-muted").first.inner_text()
                        if not price_text:
                            price_text = card.inner_text()

                        parsed_price = _extract_price_value(price_text)
                        if parsed_price is None:
                            continue
                        normalized_price: str | float = "Free" if is_free_price_text(price_text) else parsed_price

                        seen_urls.add(item_url)
                        products.append(
                            {
                                "name": name,
                                "price": normalized_price,
                                "source": provider.name,
                                "url": item_url,
                                "relevance_score": relevance,
                            }
                        )

            prices = [item["price"] for item in products if isinstance(item.get("price"), (int, float))]
            products.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    _price_sort_value(item.get("price")),
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
                url=source_url,
                row_count=row_count,
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
                url=source_url,
                stage=stage,
                error_type=type(exc).__name__,
                detail=format_exception_detail(exc),
            )
            return []
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

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
                    normalized_price: str | float = "Free" if is_free_price_text(price_text) else price
                    page_offers.append(
                        {
                            "name": game_title,
                            "price": normalized_price,
                            "source": merchant,
                            "url": redirect_url,
                            "relevance_score": score,
                        }
                    )

                if not page_offers:
                    continue

                page_offers.sort(key=lambda item: _price_sort_value(item.get("price")))
                offers.append(page_offers[0])

            offers.sort(
                key=lambda item: (
                    -int(item.get("relevance_score", 0)),
                    _price_sort_value(item.get("price")),
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
