import logging
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, FeatureNotFound
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from ..logging_utils import configure_logging, format_exception_detail, log_event
from ..locale_utils import build_accept_language, resolve_locale
from ..price_utils import extract_price_value

logger = configure_logging()

WEBKIT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
}

UNSUPPORTED_URL_SITES = {"etsy", "cardmarket"}

SITE_CONFIGS: dict[str, dict[str, list[str]]] = {
    "cyberport": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            "div[data-test-id='product-price']",
            "div.text-h2[data-test-id='product-price']",
            "[itemprop='price']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img[data-test-id='product-image']",
            "img",
        ],
    },
    "alternate": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            ".campaign-timer-price-section .price",
            ".campaign-timer-price-section [class*='price']",
            "[data-testid='price']",
            ".product-price",
            "[itemprop='price']",
            "meta[itemprop='price']",
            ".price",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "img",
        ],
    },
    "mindfactory": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            ".pprice",
            ".price",
            "[itemprop='price']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "img",
        ],
    },
    "notebooksbilliger": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            "[data-testid='price']",
            ".price",
            ".product-price",
            "[itemprop='price']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
    "amazon": {
        "title_selectors": [
            "#productTitle",
            "h1#title span",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "#corePriceDisplay_desktop_feature_div span.a-price span.a-offscreen",
            "span#priceblock_ourprice",
            "span#priceblock_dealprice",
            "span#priceblock_saleprice",
            "span.a-price.aok-align-center span.a-offscreen",
            "span.a-price .a-offscreen",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "img#landingImage",
            "img#imgBlkFront",
            "img#imgBlkBack",
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
        ],
    },
    "ebay": {
        "title_selectors": [
            "h1.x-item-title__mainTitle span",
            "h1#itemTitle",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "div.x-price-primary span.ux-textspans",
            "div.x-price-primary span",
            "span[itemprop='price']",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img#icImg",
            "img",
        ],
    },
    "etsy": {
        "title_selectors": [
            "h1[data-buy-box-listing-title='true']",
            "h1.wt-text-body-03",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "p[data-buy-box-region='price'] span.currency-value",
            "[data-buy-box-region='price'] .wt-text-title-03",
            "p.wt-text-title-03",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img[data-listing-card-listing-image]",
            "img",
        ],
    },
    "ikea": {
        "title_selectors": [
            "h1[data-testid='product-name']",
            "h1",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "span[data-testid='price']",
            ".pip-price__integer",
            ".pip-temp-price__sr-text",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img[data-testid='pip-product-image']",
            "img",
        ],
    },
    "aliexpress": {
        "title_selectors": [
            "h1[data-pl='product-title']",
            ".product-title-text",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            ".price--currentPriceText--V8_y_b5",
            "[data-pl='product-price']",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
    "geizhals": {
        "title_selectors": [
            "h1",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
            ".gh_price",
            ".price",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
    "tcgplayer": {
        "title_selectors": [
            "h1",
            ".product-details__name",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
            ".product-details__price",
            ".price",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
    "cardmarket": {
        "title_selectors": [
            "h1",
            ".page-title",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
            ".price-container",
            ".price",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
    "steam": {
        "title_selectors": [
            ".apphub_AppName",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            "meta[itemprop='price']",
            ".game_purchase_price",
            ".discount_final_price",
            ".price",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            ".game_header_image_full",
            "img",
        ],
    },
    "keyforsteam": {
        "title_selectors": [
            "h1",
            "meta[property='og:title']",
            "title",
        ],
        "price_selectors": [
            ".offers-price",
            "meta[property='product:price:amount']",
            "meta[itemprop='price']",
        ],
        "image_selectors": [
            "meta[property='og:image']",
            "meta[property='og:image:secure_url']",
            "img",
        ],
    },
}

GENERIC_TITLE_SELECTORS = ["meta[property='og:title']", "h1", "title"]
GENERIC_PRICE_SELECTORS = [
    "[data-test-id='product-price']",
    "[data-testid='price']",
    ".product-price",
    ".price",
    ".pprice",
    "[itemprop='price']",
    "meta[property='product:price:amount']",
    "meta[property='og:price:amount']",
    "meta[itemprop='price']",
]
GENERIC_IMAGE_SELECTORS = [
    "meta[property='og:image']",
    "meta[property='og:image:secure_url']",
    "meta[name='twitter:image']",
    "meta[property='twitter:image']",
    "img",
]


def _build_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except FeatureNotFound:
        # Fallback keeps scraping alive when optional lxml isn't installed.
        return BeautifulSoup(html, "html.parser")


def _build_headers(locale: str | None) -> dict[str, str]:
    headers = HEADERS.copy()
    headers["Accept-Language"] = build_accept_language(locale)
    return headers


def get_site_key(url: str) -> str | None:
    host = urlparse(url).netloc.lower()
    if "geizhals." in host:
        return "geizhals"
    if "tcgplayer.com" in host:
        return "tcgplayer"
    if "cardmarket.com" in host:
        return "cardmarket"
    if "steampowered.com" in host:
        return "steam"
    if "keyforsteam." in host:
        return "keyforsteam"
    if "amazon." in host:
        return "amazon"
    if "ebay." in host:
        return "ebay"
    if "etsy." in host:
        return "etsy"
    if "ikea." in host:
        return "ikea"
    if "aliexpress." in host:
        return "aliexpress"
    if "cyberport" in host:
        return "cyberport"
    if "alternate" in host:
        return "alternate"
    if "mindfactory" in host:
        return "mindfactory"
    if "notebooksbilliger" in host:
        return "notebooksbilliger"
    return None


def _get_site_key(url: str) -> str | None:
    return get_site_key(url)


def get_unsupported_url_sites() -> list[str]:
    return sorted(UNSUPPORTED_URL_SITES)


def is_url_site_explicitly_unsupported(url: str) -> bool:
    site_key = get_site_key(url)
    return site_key in UNSUPPORTED_URL_SITES if site_key else False


def _extract_price_from_text(text: str) -> float | None:
    return extract_price_value(text)


def extract_price(text: str) -> float | None:
    return _extract_price_from_text(text)


def _extract_title_from_soup(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    best_title = None
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            content = (node.get("content") or "").strip()
            if content:
                best_title = _choose_better_title(best_title, content)
                continue
        text = node.get_text(" ", strip=True)
        if text:
            best_title = _choose_better_title(best_title, text)
    return best_title


def _looks_like_domain_title(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    # e.g. "notebooksbilliger.de", "etsy.com"
    return "." in normalized and " " not in normalized and len(normalized) <= 64


def _choose_better_title(current: str | None, candidate: str | None) -> str | None:
    if not candidate:
        return current
    candidate = candidate.strip()
    if not candidate:
        return current
    if not current:
        return candidate

    current_domain_like = _looks_like_domain_title(current)
    candidate_domain_like = _looks_like_domain_title(candidate)
    if candidate_domain_like and not current_domain_like:
        return current
    if current_domain_like and not candidate_domain_like:
        return candidate
    return candidate if len(candidate) >= len(current) else current


def _extract_price_from_soup(soup: BeautifulSoup, selectors: list[str]) -> float | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            content = node.get("content")
            if content:
                price = _extract_price_from_text(content)
                if price is not None:
                    return price
        text = node.get_text(" ", strip=True)
        price = _extract_price_from_text(text)
        if price is not None:
            return price

    return None


def _normalize_image_candidate(value: str | None, base_url: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate or candidate.startswith("data:"):
        return None
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    if base_url and not candidate.startswith("http"):
        from urllib.parse import urljoin

        candidate = urljoin(base_url, candidate)
    if candidate and candidate.startswith("http"):
        return candidate
    return None


def _extract_image_from_soup(
    soup: BeautifulSoup, selectors: list[str], base_url: str | None
) -> str | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            content = node.get("content")
            url = _normalize_image_candidate(content, base_url)
            if url:
                return url
            continue
        if node.name != "img":
            continue
        for attr in ("data-src", "data-lazy", "data-original", "data-old-hires", "src"):
            url = _normalize_image_candidate(node.get(attr), base_url)
            if url:
                return url
        srcset = node.get("srcset") or node.get("data-srcset")
        if srcset:
            first = srcset.split(",")[0].strip().split(" ")[0]
            url = _normalize_image_candidate(first, base_url)
            if url:
                return url
    return None


def _infer_image_from_url(site_key: str | None, url: str) -> str | None:
    if site_key != "tcgplayer":
        return None
    match = re.search(r"/product/(\d+)", url)
    if not match:
        return None
    product_id = match.group(1)
    return f"https://tcgplayer-cdn.tcgplayer.com/product/{product_id}_in_1000x1000.jpg"


def _extract_keyforsteam_price(soup: BeautifulSoup) -> float | None:
    prices: list[float] = []
    for offer_node in soup.select("a.recomended_offers"):
        price_node = offer_node.select_one(".offers-price")
        price_text = price_node.get_text(" ", strip=True) if price_node else None
        price = extract_price_value(price_text)
        if price is not None:
            prices.append(price)
    if not prices:
        for row in soup.select("tr"):
            price_node = row.select_one(".offers-price")
            if not price_node:
                continue
            price_text = price_node.get_text(" ", strip=True)
            price = extract_price_value(price_text)
            if price is not None:
                prices.append(price)
    if not prices:
        for node in soup.select(".offers-price"):
            price_text = node.get_text(" ", strip=True)
            price = extract_price_value(price_text)
            if price is not None:
                prices.append(price)
    if not prices:
        return None
    return min(prices)


def _extract_media_from_json_ld(
    soup: BeautifulSoup, base_url: str | None
) -> tuple[str | None, float | None, str | None]:
    def _walk(payload):
        if isinstance(payload, dict):
            yield payload
            for value in payload.values():
                yield from _walk(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from _walk(item)

    def _extract_offer_price(offer_payload) -> float | None:
        for node in _walk(offer_payload):
            if not isinstance(node, dict):
                continue
            for key in ("price", "lowPrice", "highPrice"):
                price_value = extract_price_value(node.get(key))
                if price_value is not None:
                    return price_value
            price_spec = node.get("priceSpecification")
            if isinstance(price_spec, dict):
                price_value = extract_price_value(price_spec.get("price"))
                if price_value is not None:
                    return price_value
        return None

    def _extract_image(value) -> str | None:
        if isinstance(value, str):
            return _normalize_image_candidate(value, base_url)
        if isinstance(value, list):
            for item in value:
                url = _extract_image(item)
                if url:
                    return url
        if isinstance(value, dict):
            for key in ("url", "@id"):
                url = _normalize_image_candidate(value.get(key), base_url)
                if url:
                    return url
        return None

    fallback_name = None
    fallback_image = None
    for script in soup.select("script[type='application/ld+json']"):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        for node in _walk(payload):
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            node_types = node_type if isinstance(node_type, list) else [node_type]
            if "Product" not in node_types and "offers" not in node and "name" not in node:
                continue

            name = node.get("name")
            if isinstance(name, str):
                name = name.strip()
            else:
                name = None
            if name and fallback_name is None:
                fallback_name = name
            if fallback_image is None:
                fallback_image = _extract_image(node.get("image"))

            price = _extract_offer_price(node.get("offers")) if node.get("offers") is not None else None
            if price is None:
                price = _extract_offer_price(node)
            if price is not None:
                image = _extract_image(node.get("image")) or fallback_image
                return name or fallback_name, price, image
    return fallback_name, None, fallback_image


def scrape_with_bs4(url: str, locale: str | None = None):
    site_key = get_site_key(url)
    site_cfg = SITE_CONFIGS.get(site_key or "", {})
    title_selectors = site_cfg.get("title_selectors", []) + GENERIC_TITLE_SELECTORS
    price_selectors = site_cfg.get("price_selectors", [])
    if site_key != "alternate":
        price_selectors = price_selectors + GENERIC_PRICE_SELECTORS
    image_selectors = site_cfg.get("image_selectors", []) + GENERIC_IMAGE_SELECTORS

    headers = _build_headers(locale)
    session = requests.Session()
    try:
        response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
    except requests.RequestException as exc:
        log_event(
            logger,
            logging.WARNING,
            "scrape.url.bs4.request_failed",
            url=url,
            error_type=type(exc).__name__,
            detail=format_exception_detail(exc),
        )
        return None

    if response.status_code != 200:
        log_event(
            logger,
            logging.WARNING,
            "scrape.url.bs4.non_200",
            url=url,
            status_code=response.status_code,
        )
        return None

    soup = _build_soup(response.text)

    title = _extract_title_from_soup(soup, title_selectors) or "Unknown"
    price = _extract_price_from_soup(soup, price_selectors)
    image_url = _extract_image_from_soup(soup, image_selectors, url)
    ld_title, ld_price, ld_image = _extract_media_from_json_ld(soup, url)
    if (title == "Unknown" or _looks_like_domain_title(title)) and ld_title:
        title = ld_title
    if price is None and ld_price is not None:
        price = ld_price
    if not image_url and ld_image:
        image_url = ld_image
    if site_key == "keyforsteam":
        key_price = _extract_keyforsteam_price(soup)
        if key_price is not None:
            price = key_price
    if not image_url:
        image_url = _infer_image_from_url(site_key, url)

    if price is None:
        log_event(
            logger,
            logging.WARNING,
            "scrape.url.bs4.no_price_found",
            url=url,
            site_key=site_key,
        )
        return None

    log_event(
        logger,
        logging.DEBUG,
        "scrape.url.bs4.success",
        url=url,
        site_key=site_key,
        price=price,
    )
    return {"name": title, "price": price, "image_url": image_url, "url": url}


def scrape_with_playwright(url: str, locale: str | None = None):
    site_key = get_site_key(url)
    site_cfg = SITE_CONFIGS.get(site_key or "", {})
    title_selectors = site_cfg.get("title_selectors", []) + GENERIC_TITLE_SELECTORS
    price_selectors = site_cfg.get("price_selectors", [])
    if site_key != "alternate":
        price_selectors = price_selectors + GENERIC_PRICE_SELECTORS
    image_selectors = site_cfg.get("image_selectors", []) + GENERIC_IMAGE_SELECTORS
    headers = _build_headers(locale)
    resolved_locale = resolve_locale(locale)

    stage = "init"
    browser = None
    try:
        stage = "playwright_context"
        with sync_playwright() as p:
            stage = "browser_launch"
            use_webkit = site_key == "notebooksbilliger"
            if use_webkit:
                browser = p.webkit.launch(headless=True)
            else:
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
                user_agent=WEBKIT_USER_AGENT if use_webkit else headers["User-Agent"],
                locale=resolved_locale,
                timezone_id="Europe/Berlin",
                viewport={"width": 1366, "height": 900},
            )
            if not use_webkit:
                stage = "add_init_script"
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )

            stage = "new_page"
            page = context.new_page()
            page.set_extra_http_headers(
                {
                    "Accept-Language": headers["Accept-Language"],
                    "Referer": headers["Referer"],
                }
            )

            stage = "goto"
            page.goto(url, timeout=60000)
            stage = "wait_networkidle"
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except PlaywrightTimeoutError:
                pass

            stage = "read_title"
            title = page.title().strip() if page.title() else ""
            for selector in title_selectors:
                node = page.locator(selector).first
                if node.count() == 0:
                    continue
                candidate = node.get_attribute("content") or node.inner_text()
                candidate = candidate.strip() if candidate else ""
                if candidate:
                    title = _choose_better_title(title, candidate) or title

            stage = "extract_price_by_selectors"
            price = None
            last_seen_price_text = None
            image_url = None
            for selector in price_selectors:
                locator = page.locator(selector).first
                if locator.count() == 0:
                    continue
                content = locator.get_attribute("content")
                price_text = (content or locator.inner_text() or "").strip()
                if not price_text:
                    continue
                last_seen_price_text = price_text
                price = extract_price(price_text)
                if price is not None:
                    break

            if price is None or image_url is None:
                stage = "extract_from_html_json_ld"
                html = page.content()
                soup = _build_soup(html)
                soup_title = _extract_title_from_soup(soup, title_selectors)
                if soup_title and (not title or _looks_like_domain_title(title)):
                    title = soup_title
                if price is None:
                    price = _extract_price_from_soup(soup, price_selectors)
                if price is None and site_key == "keyforsteam":
                    price = _extract_keyforsteam_price(soup)
                if image_url is None:
                    image_url = _extract_image_from_soup(soup, image_selectors, page.url)
                ld_title, ld_price, ld_image = _extract_media_from_json_ld(soup, page.url)
                if ld_title and (not title or _looks_like_domain_title(title)):
                    title = ld_title
                if price is None and ld_price is not None:
                    price = ld_price
                if not image_url and ld_image:
                    image_url = ld_image
                if not image_url:
                    image_url = _infer_image_from_url(site_key, page.url)
                if price is None:
                    body_text = soup.get_text(" ", strip=True)
                    last_seen_price_text = (last_seen_price_text or body_text[:200]).strip()

            if price is None:
                log_event(
                    logger,
                    logging.WARNING,
                    "scrape.url.playwright.no_price_found",
                    url=url,
                    site_key=site_key,
                    price_text=last_seen_price_text,
                )
                return None

            log_event(
                logger,
                logging.DEBUG,
                "scrape.url.playwright.success",
                url=url,
                site_key=site_key,
                price=price,
            )
            return {
                "name": title or "Unknown",
                "price": price,
                "image_url": image_url,
                "url": url,
            }
    except Exception as exc:
        log_event(
            logger,
            logging.WARNING,
            "scrape.url.playwright.failed",
            url=url,
            stage=stage,
            error_type=type(exc).__name__,
            detail=format_exception_detail(exc),
        )
        return None
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass


def scrape_product_data(url: str, locale: str | None = None):
    log_event(logger, logging.INFO, "scrape.url.started", url=url)
    site_key = get_site_key(url)
    if site_key in UNSUPPORTED_URL_SITES:
        log_event(
            logger,
            logging.WARNING,
            "scrape.url.unsupported_site",
            url=url,
            site_key=site_key,
            unsupported_sites=get_unsupported_url_sites(),
        )
        return None
    result = scrape_with_bs4(url, locale=locale)

    if result:
        result.setdefault("url", url)
        log_event(logger, logging.INFO, "scrape.url.success", url=url, strategy="bs4")
        return result

    log_event(logger, logging.INFO, "scrape.url.fallback_playwright", url=url)
    playwright_result = scrape_with_playwright(url, locale=locale)
    if playwright_result:
        log_event(logger, logging.INFO, "scrape.url.success", url=url, strategy="playwright")
    else:
        log_event(logger, logging.WARNING, "scrape.url.failed_all_strategies", url=url)
    return playwright_result
