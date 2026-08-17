"""Compute all registered evaluation metrics."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .stats import (
    binary_auc,
    composed_bound_bits,
    mean,
    median,
    rate_ci_percent,
    union_bound_bits,
    wilson_interval,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _effect_count(rows: list[dict[str, str]]) -> int:
    return sum(row["service_effect"] == "true" for row in rows)


def compute_metrics(root: Path) -> dict:
    config = json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))
    proof = json.loads((root / "configs" / "proof.json").read_text(encoding="utf-8"))
    source = json.loads(
        (root / "data" / "reported" / "manuscript_tables.json").read_text(encoding="utf-8")
    )
    attacks = _read_csv(root / "data" / "manuscript_derived" / "causalcred_attack_trials.csv")
    by_testbed = defaultdict(list)
    by_group = defaultdict(list)
    for row in attacks:
        by_testbed[row["testbed"]].append(row)
        by_group[(row["testbed"], row["group"])].append(row)
    security = {
        "overall": {
            "successes": _effect_count(attacks),
            "trials": len(attacks),
            "uer_percent": 100.0 * _effect_count(attacks) / len(attacks),
            "wilson_95_percent": [100.0 * value for value in wilson_interval(_effect_count(attacks), len(attacks))],
        },
        "testbeds": {},
        "groups": {},
    }
    for testbed, rows in sorted(by_testbed.items()):
        successes = _effect_count(rows)
        security["testbeds"][testbed] = {
            "successes": successes,
            "trials": len(rows),
            "uer_percent": 100.0 * successes / len(rows),
            "wilson_95_percent": [100.0 * value for value in wilson_interval(successes, len(rows))],
        }
    for key, rows in sorted(by_group.items()):
        successes = _effect_count(rows)
        security["groups"]["/".join(key)] = {
            "successes": successes,
            "trials": len(rows),
            "uer_ci_percent": rate_ci_percent(successes, len(rows)),
        }

    injection_rows = [row for row in attacks if row["group"] == "G1"]
    model_followed = sum(row["model_followed_attacker_goal"] == "true" for row in injection_rows)
    injection = {
        "model_followed": model_followed,
        "trials": len(injection_rows),
        "rate_percent": 100.0 * model_followed / len(injection_rows),
        "protected_effects": _effect_count(injection_rows),
    }

    utility_rows = _read_csv(root / "data" / "manuscript_derived" / "benign_utility_trials.csv")
    initial_denials = sum(row["initial_policy_decision"] == "deny" for row in utility_rows)
    final_denials = sum(row["final_policy_decision"] == "deny" for row in utility_rows)
    utility = {
        "trials": len(utility_rows),
        "initial_false_denials": initial_denials,
        "initial_false_denial_percent": 100.0 * initial_denials / len(utility_rows),
        "initial_completion_percent": 100.0 * (len(utility_rows) - initial_denials) / len(utility_rows),
        "final_false_denials": final_denials,
        "final_false_denial_percent": 100.0 * final_denials / len(utility_rows),
        "final_completion_percent": 100.0 * (len(utility_rows) - final_denials) / len(utility_rows),
    }

    correction_rows = _read_csv(root / "data" / "manuscript_derived" / "a5_correction_trials.csv")
    correction = {}
    for version in ("pre_correction", "corrected"):
        rows = [row for row in correction_rows if row["implementation"] == version]
        correction[version] = {"successes": _effect_count(rows), "trials": len(rows)}

    privacy_rows = _read_csv(root / "data" / "manuscript_derived" / "privacy_presentations.csv")
    labels = [int(row["link_label"]) for row in privacy_rows]
    original_scores = [float(row["link_score_unadjusted"]) for row in privacy_rows]
    padded_scores = [float(row["link_score_padded"]) for row in privacy_rows]
    overheads = [
        float(row["padded_size_mib"]) / float(row["proof_size_mib"]) - 1.0
        for row in privacy_rows
    ]
    anonymity_rows = _read_csv(root / "data" / "manuscript_derived" / "policy_anonymity_sets.csv")
    anonymity_values = [float(row["eligible_principals"]) for row in anonymity_rows]
    privacy = {
        "presentations": len(privacy_rows),
        "class_balance": dict(sorted(Counter(labels).items())),
        "auc_unadjusted": binary_auc(labels, original_scores),
        "auc_padded": binary_auc(labels, padded_scores),
        "mean_padding_overhead_percent": 100.0 * mean(overheads),
        "policies": len(anonymity_values),
        "median_anonymity_set": median(anonymity_values),
        "policies_at_most_four": sum(value <= 4 for value in anonymity_values),
        "minimum_anonymity_set": min(anonymity_values),
    }

    component_map = proof["instruction_components_million"]
    components = [
        float(component_map[name])
        for name in ("credentials", "delegation", "attestation", "state_and_receipts", "policy", "revocation")
    ]
    instruction_total = sum(components)
    bound_terms = proof["bound_terms"]
    soundness = {
        "instruction_total_million": instruction_total,
        "instruction_shares_percent": [100.0 * value / instruction_total for value in components],
        "zk_bits": float(bound_terms["zk"]["base_bits"]),
        "mldsa_union_bits": union_bound_bits(float(bound_terms["ml_dsa"]["base_bits"]), int(bound_terms["ml_dsa"]["multiplicity"])),
        "commitment_union_bits": union_bound_bits(float(bound_terms["commitments"]["base_bits"]), int(bound_terms["commitments"]["multiplicity"])),
        "hash_union_bits": union_bound_bits(float(bound_terms["hashes"]["base_bits"]), int(bound_terms["hashes"]["multiplicity"])),
        "composed_bits": composed_bound_bits(
            [(float(term["base_bits"]), int(term["multiplicity"])) for term in bound_terms.values()]
        ),
    }

    table5 = {row[0]: row for row in source["table5"]["rows"]}
    proof_size_mib = float(table5["Proof size |π|"][1].split()[0])
    prove_seconds = float(table5["Prove"][1].split()[0])
    total_seconds = float(table5["End-to-end action latency"][1].split()[0])
    observe_ms = float(table5["Observe (one event)"][1].split()[0])
    head_ms = float(table5["Head"][1].split()[0])
    path_rate = float(config["performance_claims"]["proof_transfer_path_mbit_s"])
    transfer_seconds = proof_size_mib * 1024.0 * 1024.0 * 8.0 / (path_rate * 1_000_000.0)
    transfer_seconds_reported = round(transfer_seconds, 2)
    low_path_rate = float(config["performance_claims"]["low_bandwidth_path_mbit_s"])
    low_path_transfer = proof_size_mib * 1024.0 * 1024.0 * 8.0 / (low_path_rate * 1_000_000.0)
    cost = {
        "proof_size_mib": proof_size_mib,
        "proving_seconds": prove_seconds,
        "end_to_end_seconds": total_seconds,
        "proving_share_percent": 100.0 * prove_seconds / total_seconds,
        "transfer_seconds_80_mbit_exact": transfer_seconds,
        "transfer_seconds_80_mbit_reported": transfer_seconds_reported,
        "transfer_share_percent": 100.0 * transfer_seconds_reported / total_seconds,
        "transfer_seconds_10_mbit": low_path_transfer,
        "event_throughput_per_second_nearest_10": round((1000.0 / observe_ms) / 10.0) * 10,
        "head_throughput_per_second_nearest_10": round((1000.0 / head_ms) / 10.0) * 10,
    }

    scaling_rows = {row[0]: row for row in source["table12"]["rows"]}
    scaling = {
        "base_ms_per_million_instructions": 1000.0 * float(scaling_rows["n_c = 3 (base)"][2]) / float(scaling_rows["n_c = 3 (base)"][1]),
        "credential_range_proving_delta_seconds": float(scaling_rows["n_c = 8"][2]) - float(scaling_rows["n_c = 1"][2]),
        "delegation_range_proving_delta_seconds": float(scaling_rows["d = 8"][2]) - float(scaling_rows["d = 1"][2]),
        "policy_range_proving_delta_seconds": float(scaling_rows["n_p = 64"][2]) - float(scaling_rows["n_p = 8"][2]),
        "events_10000_proving_seconds": float(scaling_rows["n_e = 10^4"][2]),
        "events_10000_proof_mib": float(scaling_rows["n_e = 10^4"][3]),
        "compacted_10000_proving_seconds": float(scaling_rows["n_e = 10^4, compaction at 256"][2]),
        "compacted_10000_proof_mib": float(scaling_rows["n_e = 10^4, compaction at 256"][3]),
        "compacted_state_instructions_million": config["performance_claims"]["compacted_state_instructions_million"],
    }

    metrics = {
        "schema_version": 1,
        "security": security,
        "injection": injection,
        "utility": utility,
        "a5_correction": correction,
        "privacy": privacy,
        "soundness": soundness,
        "cost": cost,
        "scaling": scaling,
        "evidence_boundary": {
            "manuscript_measurements": "manuscript_summary",
            "manuscript_derived_records": "deterministic_derivation_from_manuscript_summary",
            "reference_execution": "executed_reference_runtime",
            "reference_runtime_metrics": "results/executed/reference_metrics.json",
        },
    }
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "results" / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metrics
