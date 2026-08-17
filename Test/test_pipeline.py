from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_all_tables_exist_in_three_formats(self) -> None:
        for number in range(1, 14):
            for suffix in ("csv", "md", "tex"):
                path = ROOT / "results" / "tables" / f"table{number:02d}.{suffix}"
                self.assertTrue(path.is_file(), path)

    def test_metrics_match_headline_values(self) -> None:
        metrics = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["security"]["overall"]["successes"], 0)
        self.assertEqual(metrics["security"]["overall"]["trials"], 6500)
        self.assertEqual(round(metrics["utility"]["final_completion_percent"], 1), 98.2)
        self.assertEqual(round(metrics["utility"]["final_false_denial_percent"], 2), 1.83)
        self.assertEqual(metrics["privacy"]["auc_unadjusted"], 0.641)
        self.assertEqual(metrics["privacy"]["auc_padded"], 0.512)

    def test_verification_status(self) -> None:
        report = json.loads((ROOT / "results" / "verification.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["checks_failed"], 0)

    def test_executed_reference_evidence_exists(self) -> None:
        metrics = json.loads(
            (ROOT / "results" / "executed" / "reference_metrics.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(metrics["evidence_class"], "executed_reference_runtime")
        self.assertEqual(metrics["overall"]["trials"], 6500)
        self.assertEqual(metrics["overall"]["successes"], 0)
        self.assertIn("template_clustered_bootstrap_95_percent", metrics["overall"])


if __name__ == "__main__":
    unittest.main()
