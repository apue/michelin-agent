import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from michelin_maps.domain import Restaurant
from michelin_maps.pipeline import run_import


def item(identifier):
    return Restaurant(
        identifier,
        identifier,
        identifier,
        "Bangkok",
        "Thailand",
        None,
        None,
        "Selected",
        ["Thai"],
        "Moderate",
        "",
        [identifier],
        ["Bangkok"],
    )


class FakeMapsSession:
    def __init__(self, *_args, **_kwargs):
        self.page_items = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def maybe_recycle(self):
        return None

    def mark_item(self):
        self.page_items += 1

    def recreate_after_crash(self):
        return None

    def discover(self, restaurant):
        return {
            "status": "matched",
            "detail": {"title": restaurant.name},
            "observed": [],
        }

    def save(self, _note):
        return {"saved": True, "already_in_target": False}


class PipelineTests(unittest.TestCase):
    @patch("michelin_maps.pipeline.MapsSession", FakeMapsSession)
    def test_limited_run_preserves_full_total_and_resumes_without_duplicates(self):
        items = [item("one"), item("two")]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            first = run_import(
                items, run_dir, "List", "https://maps.test/list", "http://cdp", limit=1
            )
            self.assertEqual(first["total"], 2)
            self.assertEqual(first["saved_pois"], 1)
            second = run_import(
                items, run_dir, "List", "https://maps.test/list", "http://cdp"
            )
            self.assertEqual(second["saved_pois"], 2)
            audit = json.loads((run_dir / "audit.json").read_text())
            self.assertEqual(len(audit["entries"]), 2)
            self.assertEqual(len({row["id"] for row in audit["entries"]}), 2)

    @patch("michelin_maps.pipeline.MapsSession", FakeMapsSession)
    def test_discovery_uses_isolated_artifact_directory(self):
        items = [item("one"), item("two")]
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            run_import(
                items,
                run_dir,
                "List",
                "https://maps.test/list",
                "http://cdp",
                discover_only=True,
                limit=1,
            )
            self.assertTrue((run_dir / "discovery" / "audit.json").exists())
            self.assertFalse((run_dir / "audit.json").exists())
            audit = json.loads((run_dir / "discovery" / "audit.json").read_text())
            self.assertEqual(audit["total"], 2)
            self.assertEqual(len(audit["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
