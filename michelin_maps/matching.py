from __future__ import annotations

import math
import re
from difflib import SequenceMatcher

from .domain import Candidate, Restaurant, ascii_fold, compact


def field_similarity(aliases: list[str], fields: list[str]) -> float:
    best = 0.0
    for alias in aliases:
        for field in fields:
            segments = [field, *re.split(r"[|·•,;/—–-]", field)]
            for segment in segments:
                for left, right in (
                    (compact(alias), compact(segment)),
                    (ascii_fold(compact(alias)), ascii_fold(compact(segment))),
                ):
                    if not left or not right:
                        continue
                    ratio = SequenceMatcher(None, left, right).ratio()
                    containment = (
                        1.0
                        if min(len(left), len(right)) >= 3
                        and (left in right or right in left)
                        else 0.0
                    )
                    best = max(best, ratio, containment)
    return best


def coordinates(url: str) -> tuple[float | None, float | None]:
    data_match = re.search(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)", url)
    if data_match:
        return float(data_match.group(1)), float(data_match.group(2))
    if "/maps/place/" in url:
        camera_match = re.search(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", url)
        if camera_match:
            return float(camera_match.group(1)), float(camera_match.group(2))
    return None, None


def distance_km(
    lat1: float | None, lng1: float | None, lat2: float | None, lng2: float | None
) -> float | None:
    if None in {lat1, lng1, lat2, lng2}:
        return None
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)  # type: ignore[arg-type]
    dp = math.radians(lat2 - lat1)  # type: ignore[operator]
    dl = math.radians(lng2 - lng1)  # type: ignore[operator]
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def address_matches(item: Restaurant, address: str | None) -> bool:
    haystack = ascii_fold(address or "")
    aliases = [*item.city_aliases, item.city] if item.city else [item.country]
    return any(ascii_fold(alias) in haystack for alias in aliases if alias)


def rank_candidate(item: Restaurant, candidate: Candidate) -> Candidate:
    lat, lng = coordinates(candidate.url)
    candidate.name_score = round(
        field_similarity(item.aliases, candidate.fields or [candidate.name]), 3
    )
    distance = distance_km(item.lat, item.lng, lat, lng)
    candidate.distance_km = round(distance, 3) if distance is not None else None
    candidate.city_match = address_matches(item, candidate.address)
    return candidate


def acceptable(candidate: Candidate) -> bool:
    if candidate.distance_km is not None:
        return (candidate.name_score >= 0.55 and candidate.distance_km <= 2.5) or (
            candidate.name_score >= 0.75 and candidate.distance_km <= 5.0
        )
    return candidate.direct and candidate.name_score >= 0.72 and candidate.city_match


def detail_is_restaurant(
    title: str, category: str | None, subtitles: list[str]
) -> bool:
    text = " ".join([title, category or "", *subtitles]).casefold()
    blocked = (
        "compare prices",
        "similar hotels",
        "hostel",
        "hotel room",
        "shopping mall",
    )
    return not any(marker in text for marker in blocked)
