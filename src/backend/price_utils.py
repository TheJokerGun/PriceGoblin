import re

FREE_PRICE_TERMS = {
    "kostenlos",
    "gratis",
    "free",
    "free to play",
    "free-to-play",
    "play for free",
    "0",
    "0.0",
    "0.00",
    "0,00",
    "0,0",
}

FREE_SHIPPING_CONTEXT_TERMS = {
    "shipping",
    "delivery",
    "returns",
    "return",
    "versand",
    "lieferung",
    "rueckgabe",
    "rückgabe",
}


def is_free_price_text(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.lower().split())
    if any(term in normalized for term in FREE_SHIPPING_CONTEXT_TERMS):
        return False
    if normalized in FREE_PRICE_TERMS:
        return True
    if normalized.replace(" ", "") in FREE_PRICE_TERMS:
        return True
    return False


def extract_price_value(value: str | float | int | None) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    if is_free_price_text(value):
        return 0.0

    match = re.search(r"(\d{1,3}(?:[.,\s]\d{3})*[.,]\d{2}|\d+[.,]\d{2})", value)
    if not match:
        return None
    raw = match.group(1).replace(" ", "")
    if "." in raw and "," in raw:
        # Choose decimal separator by right-most punctuation.
        if raw.rfind(",") > raw.rfind("."):
            normalized = raw.replace(".", "").replace(",", ".")
        else:
            normalized = raw.replace(",", "")
    elif "," in raw:
        left, right = raw.rsplit(",", 1)
        normalized = f"{left.replace(',', '')}.{right}" if len(right) == 2 else raw.replace(",", "")
    elif "." in raw:
        left, right = raw.rsplit(".", 1)
        normalized = f"{left}.{right}" if len(right) == 2 else raw.replace(".", "")
    else:
        normalized = raw
    try:
        return float(normalized)
    except ValueError:
        return None


def normalize_price_label(value: str | float | int | None) -> str | float | int | None:
    if is_free_price_text(value if isinstance(value, str) else None):
        return "Free"
    return value
