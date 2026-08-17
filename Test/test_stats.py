from __future__ import annotations

import unittest

from causalcred_eval.stats import (
    binary_auc,
    clustered_bootstrap_mean_interval,
    composed_bound_bits,
    union_bound_bits,
    wilson_interval,
)


class StatisticsTests(unittest.TestCase):
    def test_zero_success_wilson_interval(self) -> None:
        lower, upper = wilson_interval(0, 3250)
        self.assertEqual(round(100 * lower, 2), 0.00)
        self.assertEqual(round(100 * upper, 2), 0.12)

    def test_baseline_wilson_interval(self) -> None:
        lower, upper = wilson_interval(1184, 1500)
        self.assertEqual(round(100 * lower, 2), 76.80)
        self.assertEqual(round(100 * upper, 2), 80.92)

    def test_auc_with_ties(self) -> None:
        labels = [1] * 10 + [0] * 10
        scores = [1] * 4 + [0] * 6 + [0] * 10
        self.assertAlmostEqual(binary_auc(labels, scores), 0.7)

    def test_union_bounds(self) -> None:
        self.assertEqual(round(union_bound_bits(128, 12), 1), 124.4)
        self.assertEqual(round(union_bound_bits(192, 14), 1), 188.2)
        self.assertGreater(composed_bound_bits([(96, 1), (128, 12), (192, 14), (192, 96)]), 95.9)

    def test_clustered_bootstrap_is_deterministic_and_cluster_aware(self) -> None:
        values = [0, 0, 1, 1, 0, 0, 1, 1]
        clusters = ["a", "a", "b", "b", "c", "c", "d", "d"]
        first = clustered_bootstrap_mean_interval(
            values, clusters, iterations=500, seed="bootstrap-test"
        )
        second = clustered_bootstrap_mean_interval(
            values, clusters, iterations=500, seed="bootstrap-test"
        )
        self.assertEqual(first, second)
        self.assertLessEqual(first[0], 0.5)
        self.assertGreaterEqual(first[1], 0.5)


if __name__ == "__main__":
    unittest.main()
