DEFAULT_LOCALE = "de-DE"
DEFAULT_ACCEPT_LANGUAGE = "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"


def normalize_locale(locale: str | None) -> str | None:
    if not locale:
        return None
    value = locale.strip().replace("_", "-")
    if not value:
        return None
    parts = value.split("-")
    language = parts[0].lower()
    if len(parts) == 1:
        return language
    region = parts[1].upper() if len(parts[1]) == 2 else parts[1]
    rest = parts[2:]
    return "-".join([language, region, *rest]) if rest else f"{language}-{region}"


def resolve_locale(locale: str | None) -> str:
    return normalize_locale(locale) or DEFAULT_LOCALE


def build_accept_language(locale: str | None) -> str:
    resolved = resolve_locale(locale)
    if resolved == DEFAULT_LOCALE:
        return DEFAULT_ACCEPT_LANGUAGE
    language = resolved.split("-", 1)[0]
    return f"{resolved},{language};q=0.9,en-US;q=0.8,en;q=0.7"


def locale_region(locale: str | None) -> str | None:
    normalized = normalize_locale(locale)
    if not normalized:
        return None
    parts = normalized.split("-")
    if len(parts) >= 2 and len(parts[1]) == 2:
        return parts[1].upper()
    return None
