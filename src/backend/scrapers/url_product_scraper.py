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




def extract_price(text: str):
    match = re.search(r"(\d+[.,]\d{2})", text)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def scrape_with_bs4(url: str):
    session = requests.Session()
    response = session.get(url, headers=HEADERS, timeout=15)

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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")

        title = page.title()

        # ✅ Wait for price element explicitly
        page.wait_for_selector('[data-test-id="product-price"]', timeout=10000)

        price_element = page.locator('[data-test-id="product-price"]')
        price_text = price_element.inner_text()

        price = extract_price(price_text)

        browser.close()

        if not price:
            return None

        return {
            "name": title,
            "price": price,
            url: url
        }



def scrape_product_data(url: str):
    # 1️⃣ Try BeautifulSoup first
    result = scrape_with_bs4(url)

    if result:
        print("Used BeautifulSoup")
        return result

    # 2️⃣ Fallback to Playwright
    print("Falling back to Playwright...")
    return scrape_with_playwright(url)


