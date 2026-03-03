import logging
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from ..logging_utils import configure_logging, format_exception_detail, log_event

logger = configure_logging()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}

SITE_CONFIGS: dict[str, dict[str, list[str]]] = {
    "cyberport": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            "div[data-test-id='product-price']",
            "div.text-h2[data-test-id='product-price']",
            "[itemprop='price']",
            "meta[itemprop='price']",
        ],
    },
    "alternate": {
        "title_selectors": ["meta[property='og:title']", "h1", "title"],
        "price_selectors": [
            "[data-testid='price']",
            ".price",
            ".product-price",
            "[itemprop='price']",
            "meta[itemprop='price']",
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
    "meta[itemprop='price']",
]


def _get_site_key(url: str) -> str | None:
    host = urlparse(url).netloc.lower()
    if "cyberport" in host:
        return "cyberport"
    if "alternate" in host:
        return "alternate"
    if "mindfactory" in host:
        return "mindfactory"
    if "notebooksbilliger" in host:
        return "notebooksbilliger"
    return None


def _extract_price_from_text(text: str) -> float | None:
    match = re.search(r"(\d{1,3}(?:[.\s]\d{3})*[.,]\d{2}|\d+[.,]\d{2})", text)
    if not match:
        return None
    normalized = match.group(1).replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def extract_price(text: str) -> float | None:
    return _extract_price_from_text(text)


def _extract_title_from_soup(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            content = (node.get("content") or "").strip()
            if content:
                return content
        text = node.get_text(" ", strip=True)
        if text:
            return text
    return None


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

    return _extract_price_from_text(soup.get_text(" ", strip=True))


def scrape_with_bs4(url: str):
    site_key = _get_site_key(url)
    site_cfg = SITE_CONFIGS.get(site_key or "", {})
    title_selectors = site_cfg.get("title_selectors", []) + GENERIC_TITLE_SELECTORS
    price_selectors = site_cfg.get("price_selectors", []) + GENERIC_PRICE_SELECTORS

    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
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

    soup = BeautifulSoup(response.text, "lxml")

    title = _extract_title_from_soup(soup, title_selectors) or "Unknown"
    price = _extract_price_from_soup(soup, price_selectors)

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
    return {"name": title, "price": price, "url": url}


def scrape_with_playwright(url: str):
    site_key = _get_site_key(url)
    site_cfg = SITE_CONFIGS.get(site_key or "", {})
    title_selectors = site_cfg.get("title_selectors", []) + GENERIC_TITLE_SELECTORS
    price_selectors = site_cfg.get("price_selectors", []) + GENERIC_PRICE_SELECTORS

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
            stage = "add_init_script"
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            stage = "new_page"
            page = context.new_page()
            page.set_extra_http_headers(
                {
                    "Accept-Language": HEADERS["Accept-Language"],
                    "Referer": HEADERS["Referer"],
                }
            )

            stage = "goto"
            page.goto(url, timeout=60000)
            stage = "wait_networkidle"
            page.wait_for_load_state("networkidle")

            stage = "read_title"
            title = page.title().strip() if page.title() else ""
            for selector in title_selectors:
                node = page.locator(selector).first
                if node.count() == 0:
                    continue
                candidate = node.get_attribute("content") or node.inner_text()
                candidate = candidate.strip() if candidate else ""
                if candidate:
                    title = candidate
                    break

            stage = "extract_price_by_selectors"
            price = None
            last_seen_price_text = None
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

            if price is None:
                stage = "extract_price_from_body"
                body_text = page.locator("body").inner_text()
                price = extract_price(body_text)
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


def scrape_product_data(url: str):
    log_event(logger, logging.INFO, "scrape.url.started", url=url)
    result = scrape_with_bs4(url)

    if result:
        result.setdefault("url", url)
        log_event(logger, logging.INFO, "scrape.url.success", url=url, strategy="bs4")
        return result

    log_event(logger, logging.INFO, "scrape.url.fallback_playwright", url=url)
    playwright_result = scrape_with_playwright(url)
    if playwright_result:
        log_event(logger, logging.INFO, "scrape.url.success", url=url, strategy="playwright")
    else:
        log_event(logger, logging.WARNING, "scrape.url.failed_all_strategies", url=url)
    return playwright_result
