from __future__ import annotations

import re

from .domain import Restaurant, ascii_fold

CITY_ALIASES: dict[str, list[str]] = {
    "bangkok": ["Bangkok", "Krung Thep", "กรุงเทพมหานคร"],
    "da-nang": ["Da Nang", "Đà Nẵng"],
    "hanoi": ["Hanoi", "Ha Noi", "Hà Nội"],
    "ho-chi-minh-city": ["Ho Chi Minh City", "HCMC", "Saigon", "Hồ Chí Minh"],
    "kuala-lumpur": ["Kuala Lumpur", "KL"],
    "singapore": ["Singapore"],
}


def enrich_city_aliases(item: Restaurant, extra: list[str] | None = None) -> Restaurant:
    key = re.sub(r"[^a-z0-9]+", "-", ascii_fold(item.city)).strip("-")
    aliases = [item.city, *CITY_ALIASES.get(key, []), *(extra or [])]
    item.city_aliases = list(dict.fromkeys(alias for alias in aliases if alias))
    return item


def base_name(name: str) -> str:
    return re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", name).strip()


def query_cascade(item: Restaurant) -> list[str]:
    city = item.city or item.country
    base = base_name(item.name)
    folded = ascii_fold(base)
    slug_alias = item.slug.replace("-", " ").strip()
    candidates = [
        f"{item.name} {city}",
        f"{base} {city}",
        f"{folded} {city}",
        f"{slug_alias} {city}",
        f"{base} {item.country}",
    ]
    return list(dict.fromkeys(query.strip() for query in candidates if query.strip()))
