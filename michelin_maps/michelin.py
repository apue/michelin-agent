from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .domain import Restaurant, Scope
from .queries import enrich_city_aliases

ALGOLIA_APP_ID = "8NVHRD7ONV"
ALGOLIA_SEARCH_KEY = "3222e669cf890dc73fa5f38241117ba5"
ALGOLIA_URL = "https://8nvhrd7onv-dsn.algolia.net/1/indexes/*/queries"

ATTRIBUTES = [
    "_geoloc",
    "region",
    "area_name",
    "city",
    "country",
    "cuisines",
    "identifier",
    "michelin_award",
    "name",
    "slug",
    "price_category",
    "url",
]


@dataclass
class FetchResult:
    restaurants: list[Restaurant]
    expected_hits: int
    pages: int


class MichelinClient:
    def __init__(
        self, locale: str = "zh_CN", session: Any | None = None, timeout_s: int = 30
    ) -> None:
        self.index_name = f"prod-restaurants-{locale}"
        self.session = session or requests.Session()
        self.timeout_s = timeout_s

    def request_for(
        self, scope: Scope, page: int, hits_per_page: int = 100
    ) -> dict[str, Any]:
        return {
            "indexName": self.index_name,
            "attributesToHighlight": [],
            "attributesToRetrieve": ATTRIBUTES,
            "facetFilters": [[scope.facet_filter]],
            "filters": "status:Published",
            "hitsPerPage": hits_per_page,
            "page": page,
            "query": "",
        }

    def fetch(self, scope: Scope, hits_per_page: int = 100) -> FetchResult:
        restaurants: dict[str, Restaurant] = {}
        expected_hits = 0
        pages = 1
        for page in range(100):
            response = self.session.post(
                ALGOLIA_URL,
                params={
                    "x-algolia-application-id": ALGOLIA_APP_ID,
                    "x-algolia-api-key": ALGOLIA_SEARCH_KEY,
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": "https://guide.michelin.com",
                    "Referer": "https://guide.michelin.com/",
                    "User-Agent": "Mozilla/5.0 MichelinMapsAgent/0.2",
                },
                json={"requests": [self.request_for(scope, page, hits_per_page)]},
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            results = response.json().get("results") or []
            if len(results) != 1:
                raise RuntimeError(
                    "Michelin search returned an unexpected response shape"
                )
            result = results[0]
            expected_hits = int(result.get("nbHits") or 0)
            pages = int(result.get("nbPages") or 1)
            for hit in result.get("hits") or []:
                item = enrich_city_aliases(Restaurant.from_hit(hit))
                if not item.name or not item.id:
                    continue
                restaurants[item.id] = item
            if page + 1 >= pages:
                break
        if len(restaurants) != expected_hits:
            raise RuntimeError(
                f"Completeness check failed: expected {expected_hits} unique hits, got {len(restaurants)}"
            )
        return FetchResult(list(restaurants.values()), expected_hits, pages)
