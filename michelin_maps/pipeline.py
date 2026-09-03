from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .artifacts import COMPLETE_STATUSES, load_audit, recompute, write_run_artifacts
from .domain import Restaurant, ascii_fold
from .maps import MapsSession


def _process_one(
    session: MapsSession, item: Restaurant, discover_only: bool
) -> dict[str, Any]:
    discovery = session.discover(item)
    if discovery["status"] != "matched":
        return {
            "id": item.id,
            "name": item.name,
            "status": "unmatched",
            "note": None,
            "discovery": discovery,
        }
    if discover_only:
        return {
            "id": item.id,
            "name": item.name,
            "status": "matched",
            "note": item.note,
            "discovery": discovery,
        }
    save = session.save(item.note)
    return {
        "id": item.id,
        "name": item.name,
        "status": "saved",
        "note": item.note,
        "discovery": discovery,
        **save,
    }


def run_import(
    items: list[Restaurant],
    run_dir: Path,
    list_name: str,
    list_url: str,
    cdp: str,
    retry_incomplete: bool = False,
    discover_only: bool = False,
    limit: int | None = None,
    recycle_every: int = 25,
) -> dict[str, Any]:
    work_items = items[:limit] if limit is not None else items
    artifact_dir = run_dir / "discovery" if discover_only else run_dir
    audit_path = artifact_dir / "audit.json"
    audit = load_audit(audit_path, list_name, list_url, len(items))
    entries = audit["entries"]
    if retry_incomplete:
        entries = [row for row in entries if row.get("status") in COMPLETE_STATUSES]
    completed = {row["id"] for row in entries}
    audit["entries"] = entries
    audit["started_at_unix"] = time.time()

    with MapsSession(cdp, list_name, recycle_every=recycle_every) as session:
        for index, item in enumerate(work_items, 1):
            if item.id in completed:
                continue
            session.maybe_recycle()
            row: dict[str, Any]
            for page_attempt in range(2):
                try:
                    row = _process_one(session, item, discover_only)
                    break
                except Exception as exc:
                    if "Page crashed" in str(exc) and page_attempt == 0:
                        session.recreate_after_crash()
                        continue
                    row = {
                        "id": item.id,
                        "name": item.name,
                        "status": "error",
                        "note": None,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    break
            session.mark_item()
            entries.append(row)
            write_run_artifacts(artifact_dir, audit, items)
            print(
                json.dumps(
                    {"index": index, "name": item.name, "status": row["status"]},
                    ensure_ascii=False,
                ),
                flush=True,
            )
    audit["finished_at_unix"] = time.time()
    write_run_artifacts(artifact_dir, audit, items)
    return recompute(audit)


def _contains(expected: str, actual: str) -> bool:
    left, right = ascii_fold(expected), ascii_fold(actual)
    return left in right or right in left


def apply_reviews(
    items: list[Restaurant],
    run_dir: Path,
    list_name: str,
    list_url: str,
    reviews_path: Path,
    cdp: str,
) -> dict[str, Any]:
    audit = load_audit(run_dir / "audit.json", list_name, list_url, len(items))
    by_item = {item.id: item for item in items}
    by_entry = {row["id"]: row for row in audit["entries"]}
    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    if not isinstance(reviews, list):
        raise ValueError("Review overrides must be a JSON array")
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("Each review override must be an object")
        source_ids = review.get("source_ids")
        if (
            not isinstance(source_ids, list)
            or not source_ids
            or len(source_ids) != len(set(source_ids))
        ):
            raise ValueError("Each review needs unique, non-empty source_ids")
        if not review.get("query") and not review.get("maps_url"):
            raise ValueError("Each review needs query or maps_url")
        if (
            not str(review.get("expected_title") or "").strip()
            or not str(review.get("expected_address") or "").strip()
        ):
            raise ValueError(
                "Each review needs expected_title and expected_address guards"
            )

    with MapsSession(cdp, list_name) as session:
        for review in reviews:
            source_ids = review["source_ids"]
            if not source_ids or any(item_id not in by_item for item_id in source_ids):
                raise ValueError(f"Review has invalid source_ids: {source_ids}")
            detail = session.reviewed_place(
                str(review.get("maps_url") or review.get("query") or "")
            )
            expected_title = str(review.get("expected_title") or "")
            expected_address = str(review.get("expected_address") or "")
            if expected_title and not _contains(
                expected_title, detail.get("title") or ""
            ):
                raise RuntimeError(
                    f"Reviewed title mismatch: expected={expected_title!r}, actual={detail.get('title')!r}"
                )
            if expected_address and not _contains(
                expected_address, detail.get("address") or ""
            ):
                raise RuntimeError(
                    f"Reviewed address mismatch for {detail.get('title')}: {detail.get('address')!r}"
                )
            selected = [by_item[item_id] for item_id in source_ids]
            if review.get("note"):
                note = str(review["note"])
            elif len(selected) == 1:
                note = selected[0].note
            else:
                note = "；".join(f"{item.name}：{item.note}" for item in selected)
            save = session.save(note)
            evidence = {
                "query": review.get("query"),
                "maps_url": session.page.url,
                "actual_title": detail.get("title"),
                "actual_address": detail.get("address"),
                "expected_title": expected_title,
                "expected_address": expected_address,
                **save,
            }
            for offset, item in enumerate(selected):
                row = by_entry.get(item.id, {"id": item.id, "name": item.name})
                row.update(
                    {
                        "status": "saved" if offset == 0 else "covered_shared_poi",
                        "note": note,
                        "manual_review": evidence,
                        "shared_with": source_ids if len(source_ids) > 1 else [],
                    }
                )
                by_entry[item.id] = row
            audit["entries"] = [
                by_entry[item.id] for item in items if item.id in by_entry
            ]
            write_run_artifacts(run_dir, audit, items)
            session.mark_item()
            print(
                json.dumps(
                    {
                        "title": detail.get("title"),
                        "source_ids": source_ids,
                        "status": "saved",
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    audit["reviewed_at_unix"] = time.time()
    write_run_artifacts(run_dir, audit, items)
    return recompute(audit)
