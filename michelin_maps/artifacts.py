from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from .domain import Restaurant, Scope

COMPLETE_STATUSES = {"saved", "covered_shared_poi"}


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_manifest(
    path: Path, scope: Scope, restaurants: list[Restaurant], metadata: dict[str, Any]
) -> None:
    atomic_json(
        path,
        {
            "schema_version": 1,
            "scope": {
                "kind": scope.kind,
                "value": scope.value,
                "facet_filter": scope.facet_filter,
            },
            "metadata": metadata,
            "restaurants": [item.to_dict() for item in restaurants],
        },
    )


def load_manifest(path: Path) -> tuple[dict[str, Any], list[Restaurant]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(
        payload.get("restaurants"), list
    ):
        raise ValueError("Unsupported manifest schema")
    items = [Restaurant.from_dict(row) for row in payload["restaurants"]]
    if len({item.id for item in items}) != len(items):
        raise ValueError("Manifest contains duplicate restaurant IDs")
    return payload, items


def load_audit(path: Path, list_name: str, list_url: str, total: int) -> dict[str, Any]:
    if path.exists():
        audit = json.loads(path.read_text(encoding="utf-8"))
        if audit.get("total") != total:
            raise ValueError("Existing audit total does not match manifest")
        return audit
    return {
        "schema_version": 1,
        "list_name": list_name,
        "list_url": list_url,
        "total": total,
        "entries": [],
    }


def recompute(audit: dict[str, Any]) -> dict[str, Any]:
    counts = Counter(row.get("status") for row in audit["entries"])
    audit["saved_pois"] = counts["saved"]
    audit["covered_shared_poi"] = counts["covered_shared_poi"]
    audit["covered_restaurants"] = counts["saved"] + counts["covered_shared_poi"]
    audit["unmatched"] = counts["unmatched"]
    audit["errors"] = counts["error"]
    return audit


def write_run_artifacts(
    run_dir: Path, audit: dict[str, Any], items: list[Restaurant]
) -> None:
    recompute(audit)
    atomic_json(run_dir / "audit.json", audit)
    by_id = {item.id: item for item in items}
    unresolved = [
        row for row in audit["entries"] if row.get("status") not in COMPLETE_STATUSES
    ]
    with (run_dir / "unmatched.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "name", "city", "michelin_url", "status", "reason"],
        )
        writer.writeheader()
        for row in unresolved:
            item = by_id[row["id"]]
            writer.writerow(
                {
                    "id": item.id,
                    "name": item.name,
                    "city": item.city,
                    "michelin_url": item.michelin_url,
                    "status": row.get("status"),
                    "reason": row.get("error")
                    or row.get("reason")
                    or "no candidate passed",
                }
            )
    (run_dir / "summary.md").write_text(
        "# Michelin Maps run\n\n"
        f"- Source restaurants: {audit['total']}\n"
        f"- Covered restaurants: {audit['covered_restaurants']}\n"
        f"- Unique saved POIs: {audit['saved_pois']}\n"
        f"- Shared-POI restaurant records: {audit['covered_shared_poi']}\n"
        f"- Unmatched: {audit['unmatched']}\n"
        f"- Errors: {audit['errors']}\n"
        f"- List: {audit['list_url']}\n",
        encoding="utf-8",
    )


def validate_audit(audit: dict[str, Any], items: list[Restaurant]) -> Counter[str]:
    source_ids = {item.id for item in items}
    entry_ids = [row.get("id") for row in audit.get("entries", [])]
    if len(entry_ids) != len(set(entry_ids)):
        raise ValueError("Audit contains duplicate source IDs")
    if set(entry_ids) != source_ids:
        raise ValueError(
            f"Audit coverage mismatch: missing={sorted(source_ids - set(entry_ids))}, extra={sorted(set(entry_ids) - source_ids)}"
        )
    counts = Counter(str(row.get("status")) for row in audit["entries"])
    unresolved = set(counts) - COMPLETE_STATUSES
    if unresolved:
        raise ValueError(f"Audit has unresolved statuses: {sorted(unresolved)}")
    if any(
        not row.get("note") for row in audit["entries"] if row.get("status") == "saved"
    ):
        raise ValueError("A saved POI has an empty note")
    return counts
