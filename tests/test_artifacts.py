import json
import tempfile
import unittest
from pathlib import Path

from michelin_maps.artifacts import validate_audit, write_run_artifacts
from michelin_maps.domain import Restaurant


def item(identifier):
    return Restaurant(
        identifier,
        identifier,
        identifier,
        "Hanoi",
        "Vietnam",
        None,
        None,
        "Selected",
        ["Vietnamese"],
        "Moderate",
        "",
        [identifier],
        ["Hanoi"],
    )


class ArtifactTests(unittest.TestCase):
    def test_shared_poi_counts_coverage_separately(self):
        items = [item("hibana"), item("izakaya")]
        audit = {
            "total": 2,
            "list_name": "Test",
            "list_url": "https://maps.test/list",
            "entries": [
                {"id": "hibana", "status": "saved", "note": "combined"},
                {"id": "izakaya", "status": "covered_shared_poi", "note": "combined"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            write_run_artifacts(Path(directory), audit, items)
            persisted = json.loads((Path(directory) / "audit.json").read_text())
            self.assertEqual(persisted["saved_pois"], 1)
            self.assertEqual(persisted["covered_restaurants"], 2)
            self.assertEqual(
                (Path(directory) / "unmatched.csv").read_text().count("\n"), 1
            )
        self.assertEqual(validate_audit(audit, items)["covered_shared_poi"], 1)

    def test_unresolved_audit_fails_validation(self):
        items = [item("missing")]
        with self.assertRaisesRegex(ValueError, "unresolved"):
            validate_audit(
                {"entries": [{"id": "missing", "status": "unmatched"}]}, items
            )


if __name__ == "__main__":
    unittest.main()
