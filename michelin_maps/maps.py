from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import quote

import requests
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from .domain import Candidate, Restaurant
from .matching import acceptable, detail_is_restaurant, field_similarity, rank_candidate
from .queries import query_cascade


class MapsSession:
    def __init__(
        self, cdp: str, list_name: str, timeout_ms: int = 5000, recycle_every: int = 25
    ) -> None:
        self.cdp = cdp.rstrip("/")
        self.list_name = list_name
        self.timeout_ms = timeout_ms
        self.recycle_every = recycle_every
        self._playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.page_items = 0

    def __enter__(self) -> MapsSession:
        self._playwright = sync_playwright().start()
        try:
            self.browser = self._playwright.chromium.connect_over_cdp(
                self.cdp, timeout=30000
            )
        except Exception:
            self._close_stale_pages()
            self.browser = self._playwright.chromium.connect_over_cdp(
                self.cdp, timeout=30000
            )
        if not self.browser.contexts:
            raise RuntimeError("CDP browser has no context")
        self.context = self.browser.contexts[0]
        self.new_page()
        return self

    def __exit__(self, *_: object) -> None:
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
        if self._playwright:
            self._playwright.stop()

    def _close_stale_pages(self) -> None:
        targets = requests.get(f"{self.cdp}/json/list", timeout=5).json()
        pages = [target for target in targets if target.get("type") == "page"]
        for target in pages[1:]:
            requests.get(f"{self.cdp}/json/close/{target['id']}", timeout=5)

    def new_page(self) -> Page:
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
        if not self.context:
            raise RuntimeError("Maps session is not connected")
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page_items = 0
        return self.page

    def maybe_recycle(self) -> None:
        if self.page_items >= self.recycle_every:
            self.new_page()

    def goto_query(self, query: str, item: Restaurant | None = None) -> None:
        suffix = ""
        if item and item.lat is not None and item.lng is not None:
            suffix = f"/@{item.lat},{item.lng},16z"
        self.page.goto(
            f"https://www.google.com/maps/search/{quote(query)}{suffix}?hl=en",
            wait_until="domcontentloaded",
            timeout=10000,
        )  # type: ignore[union-attr]
        self.wait_ready()

    def wait_ready(self) -> None:
        self.page.wait_for_function(  # type: ignore[union-attr]
            """() => !!document.querySelector('h1') || !!document.querySelector("div[role='feed']") || !!document.querySelector("a[href*='/maps/place']")""",
            timeout=8000,
        )

    def ensure_place_ready(self) -> None:
        self.page.wait_for_function(  # type: ignore[union-attr]
            """() => !!document.querySelector('h1') && !!document.querySelector("button[data-value='Save'],button[data-value='Saved']")""",
            timeout=8000,
        )

    def extract_page(self) -> dict[str, Any]:
        return self.page.evaluate(  # type: ignore[union-attr]
            """() => {
              const clean = x => (x?.innerText || x?.getAttribute?.('aria-label') || '').trim();
              const title = clean(document.querySelector('h1')) || null;
              const addressNode = document.querySelector("button[data-item-id='address']");
              const address = clean(addressNode) || null;
              const links = [...document.querySelectorAll("a[href*='/maps/place']")];
              const seen = new Set(); const candidates = [];
              for (const link of links) {
                const href = link.href; if (!href || seen.has(href)) continue; seen.add(href);
                const card = link.closest("div[role='article']") || link.parentElement;
                const name = link.getAttribute('aria-label') || clean(card?.querySelector('.fontHeadlineSmall')) || clean(link);
                if (!name) continue;
                candidates.push({name, url: href, fields: [name, clean(card)], address: clean(card), direct: false});
              }
              const subtitles = [...document.querySelectorAll('h2')].slice(0, 4).map(clean).filter(Boolean);
              const category = clean(document.querySelector("button[jsaction*='category']")) || null;
              return {url: location.href, title, address, category, subtitles, candidates};
            }"""
        )

    def discover(self, item: Restaurant) -> dict[str, Any]:
        observed: list[dict[str, Any]] = []
        for query_index, query in enumerate(query_cascade(item), 1):
            try:
                self.goto_query(query, item)
                page_data = self.extract_page()
            except Exception as exc:
                if "Page crashed" in str(exc):
                    raise
                observed.append(
                    {"query": query, "error": f"{type(exc).__name__}: {exc}"}
                )
                continue
            candidates = [Candidate(**raw) for raw in page_data["candidates"]]
            if page_data.get("title") and page_data["title"] != "Results":
                candidates.insert(
                    0,
                    Candidate(
                        name=page_data["title"],
                        url=page_data["url"],
                        fields=[
                            page_data["title"],
                            *page_data.get("subtitles", [])[:2],
                        ],
                        address=page_data.get("address"),
                        category=page_data.get("category"),
                        direct=True,
                    ),
                )
            ranked = [rank_candidate(item, candidate) for candidate in candidates]
            ranked.sort(
                key=lambda row: (
                    acceptable(row),
                    row.name_score,
                    -(row.distance_km if row.distance_km is not None else 999),
                ),
                reverse=True,
            )
            observed.append(
                {
                    "query": query,
                    "page": page_data,
                    "ranked": [row.to_dict() for row in ranked[:5]],
                }
            )
            for candidate in ranked:
                if not acceptable(candidate):
                    continue
                if not candidate.direct:
                    self.page.goto(
                        candidate.url, wait_until="domcontentloaded", timeout=10000
                    )  # type: ignore[union-attr]
                self.ensure_place_ready()
                detail = self.extract_page()
                score = field_similarity(
                    item.aliases,
                    [detail.get("title") or "", *detail.get("subtitles", [])[:2]],
                )
                if score < 0.55 or not detail_is_restaurant(
                    detail.get("title") or "",
                    detail.get("category"),
                    detail.get("subtitles", []),
                ):
                    continue
                return {
                    "status": "matched",
                    "query_index": query_index,
                    "query": query,
                    "candidate": candidate.to_dict(),
                    "detail": detail,
                    "detail_name_score": round(score, 3),
                    "observed": observed,
                }
        return {"status": "unmatched", "observed": observed}

    def save(self, note: str) -> dict[str, Any]:
        linked = self.page.get_by_role("link", name=self.list_name, exact=True)  # type: ignore[union-attr]
        if linked.count() and linked.first.is_visible():
            note_box = self.page.locator(
                "textarea[aria-label='Edit note'],textarea[aria-label='Add note'],textarea[aria-label='编辑备注'],textarea[aria-label='添加备注']"
            ).first  # type: ignore[union-attr]
            note_box.wait_for(state="visible", timeout=5000)
            self._commit_note(note_box, note)
            return {"saved": True, "already_in_target": True}
        button = self.page.locator(
            "button[data-value='Save'],button[data-value='Saved']"
        ).first  # type: ignore[union-attr]
        button.click(timeout=5000)
        target = (
            self.page.locator("[role='menuitemradio']")
            .filter(has_text=self.list_name)
            .first
        )  # type: ignore[union-attr]
        target.wait_for(state="visible", timeout=5000)
        target.click(timeout=5000)
        note_box = self.page.locator(
            "textarea[aria-label='Add note'],textarea[aria-label='Edit note'],textarea[aria-label='编辑备注'],textarea[aria-label='添加备注']"
        ).first  # type: ignore[union-attr]
        note_box.wait_for(state="visible", timeout=5000)
        self._commit_note(note_box, note)
        linked.wait_for(state="visible", timeout=5000)
        return {"saved": True, "already_in_target": False}

    def _commit_note(self, note_box: Any, note: str) -> None:
        note_box.fill(note)
        note_box.press("Tab")
        self.page.wait_for_timeout(500)  # type: ignore[union-attr]
        if note_box.input_value() != note:
            raise RuntimeError("Note did not remain committed")

    def create_list(self, description: str = "") -> str:
        self.page.goto(
            "https://www.google.com/maps", wait_until="domcontentloaded", timeout=10000
        )  # type: ignore[union-attr]
        self.page.get_by_role("button", name="Saved").click(timeout=5000)  # type: ignore[union-attr]
        new_list = self.page.get_by_role(
            "button", name=re.compile("New list|新建列表", re.I)
        ).first  # type: ignore[union-attr]
        new_list.click(timeout=5000)
        dialog = self.page.get_by_role("dialog").last  # type: ignore[union-attr]
        dialog.get_by_role("textbox").nth(0).fill(self.list_name)
        if description and dialog.get_by_role("textbox").count() > 1:
            dialog.get_by_role("textbox").nth(1).fill(description)
        dialog.get_by_role("button", name=re.compile("Create|创建", re.I)).click(
            timeout=5000
        )
        self.page.get_by_role("heading", name=self.list_name).wait_for(timeout=8000)  # type: ignore[union-attr]
        return self.page.url  # type: ignore[union-attr]

    def verify_list(
        self, list_url: str, expected_notes: Counter[str]
    ) -> dict[str, Any]:
        self.page.goto(list_url, wait_until="domcontentloaded", timeout=15000)  # type: ignore[union-attr]
        heading = self.page.get_by_role(
            "heading", name=re.compile(r"\d+ places|\d+ 个地点", re.I)
        ).first  # type: ignore[union-attr]
        heading.wait_for(timeout=10000)
        text = heading.inner_text()
        match = re.search(r"(\d+)", text.replace(",", ""))
        if not match:
            raise RuntimeError(f"Could not parse list count from {text!r}")
        list_count = int(match.group(1))
        stable = 0
        for _ in range(300):
            state = self.page.evaluate(  # type: ignore[union-attr]
                """() => {const e=[...document.querySelectorAll('div')].filter(e=>e.scrollHeight>e.clientHeight+100&&e.clientHeight>300).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]; if(!e)return null; const sh=e.scrollHeight; e.scrollTop=Math.min(e.scrollTop+350,e.scrollHeight); return {top:e.scrollTop,sh,max:e.scrollHeight-e.clientHeight};}"""
            )
            if not state:
                break
            if state["top"] >= state["max"] - 2:
                self.page.wait_for_timeout(1200)  # type: ignore[union-attr]
                new_height = self.page.evaluate(
                    "() => [...document.querySelectorAll('div')].filter(e=>e.scrollHeight>e.clientHeight+100&&e.clientHeight>300).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0]?.scrollHeight"
                )  # type: ignore[union-attr]
                stable = stable + 1 if new_height == state["sh"] else 0
                if stable >= 3:
                    break
            else:
                self.page.wait_for_timeout(120)  # type: ignore[union-attr]
        values = self.page.locator(
            "textarea[aria-label='Note'],textarea[aria-label='备注']"
        ).evaluate_all("xs=>xs.map(x=>x.value)")  # type: ignore[union-attr]
        actual = Counter(values)
        if list_count != sum(expected_notes.values()) or len(values) != list_count:
            raise RuntimeError(
                f"List count mismatch: header={list_count}, loaded_notes={len(values)}, expected={sum(expected_notes.values())}"
            )
        if not all(values) or actual != expected_notes:
            raise RuntimeError(
                f"Note verification failed: missing={expected_notes - actual}, extra={actual - expected_notes}"
            )
        return {
            "list_count": list_count,
            "notes_loaded": len(values),
            "empty_notes": 0,
            "note_multiset_match": True,
        }

    def reviewed_place(self, query_or_url: str) -> dict[str, Any]:
        if query_or_url.startswith("https://"):
            self.page.goto(query_or_url, wait_until="domcontentloaded", timeout=10000)  # type: ignore[union-attr]
            self.wait_ready()
        else:
            self.goto_query(query_or_url)
        self.ensure_place_ready()
        return self.extract_page()

    def mark_item(self) -> None:
        self.page_items += 1

    def recreate_after_crash(self) -> None:
        self.new_page()
