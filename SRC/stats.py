"""Statistical functions used by the evaluation."""

from __future__ import annotations

import hashlib
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Return a two-sided Wilson score interval as proportions."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be in [0, trials]")
    phat = successes / trials
    denominator = 1.0 + (z * z) / trials
    center = (phat + (z * z) / (2.0 * trials)) / denominator
    margin = (
        z
        * math.sqrt(phat * (1.0 - phat) / trials + (z * z) / (4.0 * trials * trials))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def rate_ci_percent(successes: int, trials: int) -> str:
    """Format a rate and Wilson interval using manuscript precision."""
    lower, upper = wilson_interval(successes, trials)
    rate = 100.0 * successes / trials
    return f"{rate:.2f} [{100.0 * lower:.2f}, {100.0 * upper:.2f}]"


def binary_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Compute ROC AUC with half credit for tied positive-negative pairs."""
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must have equal nonzero length")
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for label, score in zip(labels, scores, strict=True):
        if label not in (0, 1):
            raise ValueError("labels must be binary")
        groups[float(score)][label] += 1
    negatives_below = 0
    favourable_pairs = 0.0
    positive_total = sum(group[1] for group in groups.values())
    negative_total = sum(group[0] for group in groups.values())
    if positive_total == 0 or negative_total == 0:
        raise ValueError("both classes are required")
    for score in sorted(groups):
        negatives, positives = groups[score]
        favourable_pairs += positives * negatives_below
        favourable_pairs += 0.5 * positives * negatives
        negatives_below += negatives
    return favourable_pairs / (positive_total * negative_total)


def median(values: Sequence[float]) -> float:
    """Return the median of a nonempty numeric sequence."""
    if not values:
        raise ValueError("values must be nonempty")
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def mean(values: Sequence[float]) -> float:
    """Return the arithmetic mean."""
    if not values:
        raise ValueError("values must be nonempty")
    return math.fsum(float(value) for value in values) / len(values)


def union_bound_bits(base_bits: float, multiplicity: int) -> float:
    """Return -log2(multiplicity * 2^-base_bits)."""
    if multiplicity <= 0:
        raise ValueError("multiplicity must be positive")
    return float(base_bits) - math.log2(multiplicity)


def composed_bound_bits(terms: Iterable[tuple[float, int]]) -> float:
    """Return -log2 of a sum of multiplicity-weighted powers of two."""
    probabilities = [multiplicity * (2.0 ** (-bits)) for bits, multiplicity in terms]
    return -math.log2(math.fsum(probabilities))


def percentile(values: Sequence[float], probability: float) -> float:
    """Return a linearly interpolated percentile of a nonempty sequence."""
    if not values:
        raise ValueError("values must be nonempty")
    if probability < 0.0 or probability > 1.0:
        raise ValueError("probability must be in [0, 1]")
    ordered = sorted(float(value) for value in values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def clustered_bootstrap_mean_interval(
    values: Sequence[float],
    clusters: Sequence[str],
    *,
    iterations: int = 2000,
    confidence: float = 0.95,
    seed: str = "causalcred-cluster-bootstrap-v1",
) -> tuple[float, float]:
    """Return a deterministic percentile interval from cluster resampling.

    Entire clusters are sampled with replacement. All observations belonging
    to a selected cluster are retained, preserving within-template dependence.
    """
    if len(values) != len(clusters) or not values:
        raise ValueError("values and clusters must have equal nonzero length")
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must be in (0, 1)")
    grouped: dict[str, list[float]] = defaultdict(list)
    for value, cluster in zip(values, clusters, strict=True):
        grouped[str(cluster)].append(float(value))
    cluster_ids = sorted(grouped)
    random_seed = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:16], "big")
    generator = random.Random(random_seed)
    estimates = []
    for _ in range(iterations):
        sampled_values: list[float] = []
        for _ in cluster_ids:
            selected = cluster_ids[generator.randrange(len(cluster_ids))]
            sampled_values.extend(grouped[selected])
        estimates.append(mean(sampled_values))
    alpha = 1.0 - confidence
    return percentile(estimates, alpha / 2.0), percentile(estimates, 1.0 - alpha / 2.0)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
