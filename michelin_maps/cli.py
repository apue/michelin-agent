from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .artifacts import load_manifest, validate_audit, write_manifest
from .domain import Scope
from .maps import MapsSession
from .michelin import MichelinClient
from .pipeline import apply_reviews, run_import


def _add_browser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cdp", default="http://127.0.0.1:9223", help="Chrome DevTools endpoint"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="michelin-maps",
        description="Agent-operated Michelin Guide to Google Maps Saved pipeline",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser(
        "fetch", help="Fetch a complete Michelin city, region, or country selection"
    )
    fetch.add_argument(
        "--scope",
        required=True,
        help="city:bangkok, region:penang, or country:malaysia",
    )
    fetch.add_argument("--run-dir", type=Path, required=True)
    fetch.add_argument("--locale", default="zh_CN")

    create = commands.add_parser(
        "create-list", help="Create an empty native Google Maps list"
    )
    create.add_argument("--list-name", required=True)
    create.add_argument("--description", default="")
    _add_browser(create)

    run = commands.add_parser("run", help="Run or resume the automatic Maps import")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--run-dir", type=Path, required=True)
    run.add_argument("--list-name", required=True)
    run.add_argument("--list-url", required=True)
    run.add_argument("--retry-incomplete", action="store_true")
    run.add_argument("--discover-only", action="store_true")
    run.add_argument("--limit", type=int)
    run.add_argument("--recycle-every", type=int, default=25)
    _add_browser(run)

    review = commands.add_parser(
        "apply-reviews", help="Save agent-reviewed long-tail mappings"
    )
    review.add_argument("--manifest", type=Path, required=True)
    review.add_argument("--run-dir", type=Path, required=True)
    review.add_argument("--reviews", type=Path, required=True)
    review.add_argument("--list-name", required=True)
    review.add_argument("--list-url", required=True)
    _add_browser(review)

    verify = commands.add_parser(
        "verify", help="Verify coverage and optionally the live Google Maps list"
    )
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--run-dir", type=Path, required=True)
    verify.add_argument("--list-name")
    verify.add_argument("--list-url")
    verify.add_argument("--offline-only", action="store_true")
    _add_browser(verify)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "fetch":
        scope = Scope.parse(args.scope)
        result = MichelinClient(locale=args.locale).fetch(scope)
        args.run_dir.mkdir(parents=True, exist_ok=True)
        path = args.run_dir / "manifest.json"
        write_manifest(
            path,
            scope,
            result.restaurants,
            {
                "expected_hits": result.expected_hits,
                "pages": result.pages,
                "locale": args.locale,
            },
        )
        print(
            json.dumps(
                {
                    "manifest": str(path),
                    "restaurants": len(result.restaurants),
                    "pages": result.pages,
                },
                ensure_ascii=False,
            )
        )
        return
    if args.command == "create-list":
        with MapsSession(args.cdp, args.list_name) as session:
            url = session.create_list(args.description)
        print(
            json.dumps(
                {"list_name": args.list_name, "list_url": url}, ensure_ascii=False
            )
        )
        return

    _, items = load_manifest(args.manifest)
    if args.command == "run":
        audit = run_import(
            items,
            args.run_dir,
            args.list_name,
            args.list_url,
            args.cdp,
            args.retry_incomplete,
            args.discover_only,
            args.limit,
            args.recycle_every,
        )
        print(
            json.dumps(
                {
                    key: audit[key]
                    for key in (
                        "total",
                        "saved_pois",
                        "covered_restaurants",
                        "unmatched",
                        "errors",
                    )
                },
                ensure_ascii=False,
            )
        )
    elif args.command == "apply-reviews":
        audit = apply_reviews(
            items, args.run_dir, args.list_name, args.list_url, args.reviews, args.cdp
        )
        print(
            json.dumps(
                {
                    key: audit[key]
                    for key in (
                        "total",
                        "saved_pois",
                        "covered_restaurants",
                        "unmatched",
                        "errors",
                    )
                },
                ensure_ascii=False,
            )
        )
    elif args.command == "verify":
        audit = json.loads((args.run_dir / "audit.json").read_text(encoding="utf-8"))
        counts = validate_audit(audit, items)
        result: dict[str, object] = {"offline": "ok", "statuses": dict(counts)}
        if not args.offline_only:
            list_name = args.list_name or audit.get("list_name")
            list_url = args.list_url or audit.get("list_url")
            if not list_name or not list_url:
                raise ValueError("Live verification needs list name and URL")
            expected = Counter(
                row["note"] for row in audit["entries"] if row["status"] == "saved"
            )
            with MapsSession(args.cdp, list_name) as session:
                result["live"] = session.verify_list(list_url, expected)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
