from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ScopeKind = Literal["city", "region", "country"]


def ascii_fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold().replace("đ", "d")
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", ascii_fold(value)).strip("-")


def compact(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKC", value).casefold().replace("đ", "d")
        if ch.isalnum()
    )


@dataclass(frozen=True)
class Scope:
    kind: ScopeKind
    value: str

    @classmethod
    def parse(cls, raw: str) -> Scope:
        try:
            kind, value = raw.split(":", 1)
        except ValueError as exc:
            raise ValueError(
                "Scope must use KIND:VALUE, for example country:vietnam"
            ) from exc
        if kind not in {"city", "region", "country"} or not value.strip():
            raise ValueError(
                "Scope kind must be city, region, or country and value cannot be empty"
            )
        return cls(kind=kind, value=value.strip())  # type: ignore[arg-type]

    @property
    def slug(self) -> str:
        return slugify(self.value)

    @property
    def facet_filter(self) -> str:
        field = {
            "city": "city.slug",
            "region": "region.slug",
            "country": "country.cname",
        }[self.kind]
        return f"{field}:{self.slug}"


def _label(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("name", "label", "slug"):
            if value.get(key):
                return str(value[key])
    return ""


def _labels(value: Any) -> list[str]:
    if not isinstance(value, list):
        return [_label(value)] if _label(value) else []
    return [label for item in value if (label := _label(item))]


@dataclass
class Restaurant:
    id: str
    name: str
    slug: str
    city: str
    country: str
    lat: float | None
    lng: float | None
    award: str
    cuisines: list[str]
    price: str
    michelin_url: str
    aliases: list[str] = field(default_factory=list)
    city_aliases: list[str] = field(default_factory=list)

    @classmethod
    def from_hit(cls, hit: dict[str, Any]) -> Restaurant:
        name = str(hit.get("name") or "").strip()
        slug = str(hit.get("slug") or slugify(name)).strip()
        city = _label(hit.get("city")) or _label(hit.get("region"))
        country_obj = hit.get("country") or {}
        country = _label(country_obj)
        if isinstance(country_obj, dict):
            country = str(
                country_obj.get("name")
                or country_obj.get("cname")
                or country_obj.get("slug")
                or country
            )
        geoloc = hit.get("_geoloc") or {}
        url = str(hit.get("url") or "")
        if url.startswith("/"):
            url = f"https://guide.michelin.com{url}"
        stable_id = hit.get("identifier") or hit.get("objectID")
        restaurant_id = (
            str(stable_id)
            if stable_id
            else f"{slugify(city)}--{slug or hashlib.sha1(name.encode('utf-8')).hexdigest()[:12]}"
        )
        slug_alias = slug.replace("-", " ").strip()
        aliases = list(dict.fromkeys(filter(None, [name, slug_alias])))
        return cls(
            id=restaurant_id,
            name=name,
            slug=slug,
            city=city,
            country=country,
            lat=float(geoloc["lat"]) if geoloc.get("lat") is not None else None,
            lng=float(geoloc["lng"]) if geoloc.get("lng") is not None else None,
            award=_label(hit.get("michelin_award")) or "Michelin Selected",
            cuisines=_labels(hit.get("cuisines")),
            price=_label(hit.get("price_category"))
            or str(hit.get("price_category") or "Unspecified"),
            michelin_url=url,
            aliases=aliases,
            city_aliases=[city] if city else [],
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Restaurant:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def note(self) -> str:
        cuisine = "、".join(self.cuisines) if self.cuisines else "未注明菜系"
        return f"{self.award}｜{cuisine}｜{self.price}"


@dataclass
class Candidate:
    name: str
    url: str
    fields: list[str] = field(default_factory=list)
    address: str | None = None
    direct: bool = False
    category: str | None = None
    name_score: float = 0.0
    distance_km: float | None = None
    city_match: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
