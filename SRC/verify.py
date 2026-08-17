"""Cross-check every registered manuscript result."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from .stats import sha256_file
from .model import ATTACKS, Control


MANUSCRIPT_SHA256 = "5f6ab37b348a15c6e4129b73ec4c42fe04760808c72cdf2daa5ea20686049d40"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _effects(rows: list[dict[str, str]]) -> int:
    return sum(row["service_effect"] == "true" for row in rows)


def _close(observed: float, expected: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(observed), float(expected), rel_tol=tolerance, abs_tol=tolerance)


def verify_all(root: Path) -> dict:
    config = json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))
    attack_registry = json.loads((root / "configs" / "attack_registry.json").read_text(encoding="utf-8"))
    testbeds = json.loads((root / "configs" / "testbeds.json").read_text(encoding="utf-8"))
    metrics = json.loads((root / "results" / "metrics.json").read_text(encoding="utf-8"))
    checks: list[dict] = []

    def check(identifier: str, condition: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "id": identifier,
                "pass": bool(condition),
                "observed": observed,
                "expected": expected,
            }
        )

    attacks = _read_csv(root / "data" / "manuscript_derived" / "causalcred_attack_trials.csv")
    check("trial-total", len(attacks) == 6500, len(attacks), 6500)
    registry_projection = [
        (entry["group"], entry["id"], entry["name"], entry["primary_control"])
        for entry in attack_registry["families"]
    ]
    model_projection = [
        (entry.group, entry.attack_id, entry.name, entry.primary_control.value) for entry in ATTACKS
    ]
    check("attack-registry-model", registry_projection == model_projection, registry_projection, model_projection)
    for testbed in ("cloud", "supply_chain"):
        rows = [row for row in attacks if row["testbed"] == testbed]
        check(f"{testbed}-trial-total", len(rows) == 3250, len(rows), 3250)
        check(f"{testbed}-effects", _effects(rows) == 0, _effects(rows), 0)
        upper = metrics["security"]["testbeds"][testbed]["wilson_95_percent"][1]
        check(f"{testbed}-wilson-upper", round(upper, 2) == 0.12, round(upper, 2), 0.12)
        expected_groups = {"G1": 1500, "G2": 750, "G3": 1000}
        check(
            f"{testbed}-manifest-allocation",
            testbeds[testbed]["group_trials"] == expected_groups,
            testbeds[testbed]["group_trials"],
            expected_groups,
        )
        for group, expected in expected_groups.items():
            observed = sum(row["group"] == group for row in rows)
            check(f"{testbed}-{group}-allocation", observed == expected, observed, expected)
    check("overall-effects", _effects(attacks) == 0, _effects(attacks), 0)

    executed_index = _read_csv(root / "data" / "executed" / "protocol_trial_index.csv")
    executed_record_files = sorted((root / "data" / "executed" / "trials").glob("*.jsonl"))
    executed_records = [record for path in executed_record_files for record in _read_jsonl(path)]
    check("executed-record-file-count", len(executed_record_files) == 26, len(executed_record_files), 26)
    check("executed-trial-total", len(executed_index) == 6500, len(executed_index), 6500)
    check(
        "executed-record-total", len(executed_records) == len(executed_index), len(executed_records), len(executed_index)
    )
    executed_effects = sum(row["service_effect"] == "true" for row in executed_index)
    check("executed-effects", executed_effects == 0, executed_effects, 0)
    allocation = defaultdict(int)
    for row in executed_index:
        allocation[(row["testbed"], row["attack_id"])] += 1
    check(
        "executed-family-allocation",
        set(allocation.values()) == {250} and len(allocation) == 26,
        {"cells": len(allocation), "counts": sorted(set(allocation.values()))},
        {"cells": 26, "counts": [250]},
    )
    valid_digests = all(
        len(row["statement_digest"]) == 64
        and all(character in "0123456789abcdef" for character in row["statement_digest"])
        for row in executed_index
    )
    check("executed-statement-digests", valid_digests, valid_digests, True)
    check(
        "executed-evidence-class",
        {row["evidence_class"] for row in executed_index} == {"executed_reference_runtime"},
        sorted({row["evidence_class"] for row in executed_index}),
        ["executed_reference_runtime"],
    )

    executed_metrics = json.loads(
        (root / "results" / "executed" / "reference_metrics.json").read_text(encoding="utf-8")
    )
    check(
        "executed-metrics-total",
        executed_metrics["overall"]["trials"] == len(executed_index),
        executed_metrics["overall"]["trials"],
        len(executed_index),
    )
    check(
        "executed-metrics-effects",
        executed_metrics["overall"]["successes"] == executed_effects,
        executed_metrics["overall"]["successes"],
        executed_effects,
    )
    bootstrap_interval = executed_metrics["overall"]["template_clustered_bootstrap_95_percent"]
    check(
        "executed-cluster-bootstrap",
        len(bootstrap_interval) == 2 and bootstrap_interval[0] <= bootstrap_interval[1],
        bootstrap_interval,
        "ordered two-value interval",
    )

    executed_ablations = _read_jsonl(root / "data" / "executed" / "control_ablations.jsonl")
    ablation_controls = {row["removed_control"] for row in executed_ablations}
    check(
        "executed-ablation-controls",
        ablation_controls == {control.value for control in Control},
        sorted(ablation_controls),
        sorted(control.value for control in Control),
    )
    full_effects = sum(row["full_service_effect"] for row in executed_ablations)
    removed_effects = sum(row["ablated_service_effect"] for row in executed_ablations)
    check("executed-ablation-full-effects", full_effects == 0, full_effects, 0)
    check(
        "executed-ablation-removed-effects",
        removed_effects == len(executed_ablations),
        removed_effects,
        len(executed_ablations),
    )

    executed_baselines = _read_jsonl(root / "data" / "executed" / "baseline_trials.jsonl")
    reference_rows = [row for row in executed_baselines if row["profile"] == "R5-causalcred-reference"]
    weak_rows = [row for row in executed_baselines if row["profile"] != "R5-causalcred-reference"]
    check(
        "executed-reference-baseline-effects",
        sum(row["service_effect"] for row in reference_rows) == 0,
        sum(row["service_effect"] for row in reference_rows),
        0,
    )
    check(
        "executed-weaker-baseline-effects",
        sum(row["service_effect"] for row in weak_rows) > 0,
        sum(row["service_effect"] for row in weak_rows),
        "> 0",
    )

    provenance = json.loads(
        (root / "environment" / "execution_provenance.json").read_text(encoding="utf-8")
    )
    source_revision = provenance["source"]["source_revision_sha256"]
    check(
        "source-revision",
        len(source_revision) == 64 and all(character in "0123456789abcdef" for character in source_revision),
        source_revision,
        "64-character SHA-256",
    )
    check(
        "model-identifier",
        provenance["execution"]["model_identifier"] == "deterministic-policy-agent-v1",
        provenance["execution"]["model_identifier"],
        "deterministic-policy-agent-v1",
    )

    benchmark_path = root / "results" / "benchmarks" / "reference_runtime_samples.csv"
    benchmark_rows = _read_csv(benchmark_path) if benchmark_path.is_file() else []
    check("benchmark-sample-count", len(benchmark_rows) == 100, len(benchmark_rows), 100)
    benchmark_valid = bool(benchmark_rows) and all(int(row["elapsed_ns"]) > 0 for row in benchmark_rows)
    check("benchmark-samples-positive", benchmark_valid, benchmark_valid, True)

    injection = metrics["injection"]
    check("injection-trials", injection["trials"] == 3000, injection["trials"], 3000)
    check("injection-followed", injection["model_followed"] == 1842, injection["model_followed"], 1842)
    check("injection-rate", _close(injection["rate_percent"], 61.4), injection["rate_percent"], 61.4)
    check("injection-effects", injection["protected_effects"] == 0, injection["protected_effects"], 0)

    utility = metrics["utility"]
    check("utility-initial-denials", utility["initial_false_denials"] == 401, utility["initial_false_denials"], 401)
    check("utility-initial-fdr", round(utility["initial_false_denial_percent"], 2) == 6.17, round(utility["initial_false_denial_percent"], 2), 6.17)
    check("utility-initial-completion", round(utility["initial_completion_percent"], 1) == 93.8, round(utility["initial_completion_percent"], 1), 93.8)
    check("utility-final-denials", utility["final_false_denials"] == 119, utility["final_false_denials"], 119)
    check("utility-final-fdr", round(utility["final_false_denial_percent"], 2) == 1.83, round(utility["final_false_denial_percent"], 2), 1.83)
    check("utility-final-completion", round(utility["final_completion_percent"], 1) == 98.2, round(utility["final_completion_percent"], 1), 98.2)

    correction = metrics["a5_correction"]
    check("a5-pre-correction", correction["pre_correction"]["successes"] == 4, correction["pre_correction"]["successes"], 4)
    check("a5-corrected", correction["corrected"]["successes"] == 0, correction["corrected"]["successes"], 0)

    baselines = _read_csv(root / "data" / "manuscript_derived" / "cloud_baseline_trials.csv")
    for baseline_id, baseline in config["baseline_cloud"].items():
        for group in ("G1", "G2", "G3"):
            specification = baseline[group]
            if not isinstance(specification, dict):
                continue
            rows = [row for row in baselines if row["baseline_id"] == baseline_id and row["group"] == group]
            observed = {"successes": _effects(rows), "trials": len(rows)}
            expected = {"successes": specification["successes"], "trials": specification["trials"]}
            check(f"baseline-{baseline_id}-{group}", observed == expected, observed, expected)

    ablations = _read_csv(root / "data" / "manuscript_derived" / "cloud_ablation_trials.csv")
    for ablation_id, specification in config["ablations"].items():
        rows = [row for row in ablations if row["ablation_id"] == ablation_id]
        observed = {"successes": _effects(rows), "trials": len(rows)}
        expected = {"successes": specification["successes"], "trials": specification["trials"]}
        check(f"ablation-{ablation_id}", observed == expected, observed, expected)
    for ablation_id, parts in config["ablation_decomposition"].items():
        observed = sum(parts.values())
        expected = config["ablations"][ablation_id]["successes"]
        check(f"ablation-{ablation_id}-decomposition", observed == expected, observed, expected)

    subset = _read_csv(root / "data" / "manuscript_derived" / "supply_chain_digest_subset.csv")
    speranza_rows = [row for row in subset if row["mechanism"] == "Speranza-style"]
    causal_rows = [row for row in subset if row["mechanism"] == "CausalCred"]
    check("speranza-digest", (_effects(speranza_rows), len(speranza_rows)) == (241, 250), [_effects(speranza_rows), len(speranza_rows)], [241, 250])
    check("causalcred-digest", (_effects(causal_rows), len(causal_rows)) == (0, 250), [_effects(causal_rows), len(causal_rows)], [0, 250])

    privacy = metrics["privacy"]
    check("privacy-presentations", privacy["presentations"] == 40000, privacy["presentations"], 40000)
    check("privacy-auc", _close(privacy["auc_unadjusted"], 0.641), privacy["auc_unadjusted"], 0.641)
    check("privacy-padded-auc", _close(privacy["auc_padded"], 0.512), privacy["auc_padded"], 0.512)
    check("privacy-padding-overhead", round(privacy["mean_padding_overhead_percent"], 1) == 14.6, round(privacy["mean_padding_overhead_percent"], 1), 14.6)
    check("privacy-policy-count", privacy["policies"] == 16, privacy["policies"], 16)
    check("privacy-median-set", privacy["median_anonymity_set"] == 1842, privacy["median_anonymity_set"], 1842)
    check("privacy-small-sets", privacy["policies_at_most_four"] == 3, privacy["policies_at_most_four"], 3)
    check("privacy-minimum-set", privacy["minimum_anonymity_set"] == 1, privacy["minimum_anonymity_set"], 1)

    soundness = metrics["soundness"]
    check("instruction-total", _close(soundness["instruction_total_million"], 208.3), soundness["instruction_total_million"], 208.3)
    expected_shares = [26.5, 14.1, 9.2, 30.1, 11.7, 8.4]
    observed_shares = [round(value, 1) for value in soundness["instruction_shares_percent"]]
    check("instruction-shares", observed_shares == expected_shares, observed_shares, expected_shares)
    check("mldsa-bound", round(soundness["mldsa_union_bits"], 1) == 124.4, round(soundness["mldsa_union_bits"], 1), 124.4)
    check("commitment-bound", round(soundness["commitment_union_bits"], 1) == 188.2, round(soundness["commitment_union_bits"], 1), 188.2)
    check("hash-bound", round(soundness["hash_union_bits"], 1) == 185.4, round(soundness["hash_union_bits"], 1), 185.4)
    check("composed-bound", soundness["composed_bits"] > 95.9, soundness["composed_bits"], "> 95.9 bits")

    cost = metrics["cost"]
    check("cost-proving-share", round(cost["proving_share_percent"], 1) == 87.3, round(cost["proving_share_percent"], 1), 87.3)
    check("cost-transfer-share", round(cost["transfer_share_percent"], 1) == 5.3, round(cost["transfer_share_percent"], 1), 5.3)
    check("cost-transfer-10mbit", round(cost["transfer_seconds_10_mbit"], 2) == 4.05, round(cost["transfer_seconds_10_mbit"], 2), 4.05)
    check("cost-event-throughput", cost["event_throughput_per_second_nearest_10"] == 2380, cost["event_throughput_per_second_nearest_10"], 2380)
    check("cost-head-throughput", cost["head_throughput_per_second_nearest_10"] == 1640, cost["head_throughput_per_second_nearest_10"], 1640)

    scaling = metrics["scaling"]
    check("scaling-base-rate", round(scaling["base_ms_per_million_instructions"], 1) == 40.4, round(scaling["base_ms_per_million_instructions"], 1), 40.4)
    check("scaling-credential-delta", _close(scaling["credential_range_proving_delta_seconds"], 5.21), scaling["credential_range_proving_delta_seconds"], 5.21)
    check("scaling-delegation-delta", _close(scaling["delegation_range_proving_delta_seconds"], 4.15), scaling["delegation_range_proving_delta_seconds"], 4.15)
    check("scaling-policy-delta", _close(scaling["policy_range_proving_delta_seconds"], 3.43), scaling["policy_range_proving_delta_seconds"], 3.43)
    check("scaling-uncompacted-10000", [scaling["events_10000_proving_seconds"], scaling["events_10000_proof_mib"]] == [176.5, 22.13], [scaling["events_10000_proving_seconds"], scaling["events_10000_proof_mib"]], [176.5, 22.13])
    check("scaling-compacted-10000", [scaling["compacted_10000_proving_seconds"], scaling["compacted_10000_proof_mib"], scaling["compacted_state_instructions_million"]] == [11.07, 5.54, 128.3], [scaling["compacted_10000_proving_seconds"], scaling["compacted_10000_proof_mib"], scaling["compacted_state_instructions_million"]], [11.07, 5.54, 128.3])

    table_files = sorted((root / "results" / "tables").glob("table*.csv"))
    check("table-count", len(table_files) == 13, len(table_files), 13)
    for number in range(1, 14):
        expected = [root / "results" / "tables" / f"table{number:02d}.{suffix}" for suffix in ("csv", "md", "tex")]
        missing = [str(path.relative_to(root)) for path in expected if not path.is_file()]
        check(f"table-{number:02d}-formats", not missing, missing, [])
    check("result-index", (root / "RESULTS_INDEX.md").is_file(), (root / "RESULTS_INDEX.md").is_file(), True)
    paper_digest = sha256_file(root / "paper" / "CausalCred_ASIACCS2027.pdf")
    check("manuscript-sha256", paper_digest == MANUSCRIPT_SHA256, paper_digest, MANUSCRIPT_SHA256)

    failures = [entry for entry in checks if not entry["pass"]]
    report = {
        "schema_version": 1,
        "status": "PASS" if not failures else "FAIL",
        "checks_passed": len(checks) - len(failures),
        "checks_failed": len(failures),
        "checks": checks,
    }
    (root / "results" / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if failures:
        identifiers = ", ".join(entry["id"] for entry in failures)
        raise RuntimeError(f"verification failed: {identifiers}")
    return report


def write_manifest(root: Path) -> None:
    exclusions = {"MANIFEST.sha256"}
    paths = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not path.is_file():
            continue
        if relative.name in exclusions or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if ".git" in relative.parts or "tmp" in relative.parts:
            continue
        paths.append(path)
    lines = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(paths)]
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
