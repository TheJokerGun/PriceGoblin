import requests
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}




def extract_price(text: str) -> float | None:
    match = re.search(r"(\d+[.,]\d{2})", text)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def scrape_with_bs4(url: str):
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")

    title = soup.title.string.strip() if soup.title else "Unknown"

    price_element = soup.find("div", {"data-test-id": "product-price"})
    price = None

    if price_element:
        price = extract_price(price_element.get_text())

    if not price:
        price = extract_price(soup.get_text())

    if not price:
        return None

    return {"name": title, "price": price}


def scrape_with_playwright(url: str):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            title = page.title()

            page.wait_for_selector('[data-test-id="product-price"]', timeout=10000)

            price_element = page.locator('div.text-h2[data-test-id="product-price"]').first
            price_text = price_element.inner_text()

            price = extract_price(price_text)

            browser.close()

            if not price:
                return None

            return {
                "name": title,
                "price": price,
                "url": url
            }
    except Exception:
        return None



def scrape_product_data(url: str):
    result = scrape_with_bs4(url)

    if result:
        result.setdefault("url", url)
        return result

    return scrape_with_playwright(url)
