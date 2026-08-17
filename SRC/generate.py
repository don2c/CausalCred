"""Deterministic construction of the evaluation records."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .model import ATTACKS, ATTACK_BY_ID, Control, controls_without, evaluate_attack


def load_config(root: Path) -> dict:
    return json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))


def _rank(seed: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{value}".encode("utf-8")).hexdigest()


def quota_selection(values: Iterable[str], count: int, seed: str) -> frozenset[str]:
    ordered = sorted(values, key=lambda value: (_rank(seed, value), value))
    if count < 0 or count > len(ordered):
        raise ValueError("quota count outside candidate range")
    return frozenset(ordered[:count])


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _attack_trial_ids(config: dict, testbed: str) -> list[tuple[str, str, str, int]]:
    count = int(config["trials_per_family_per_testbed"])
    return [
        (f"{testbed}-{attack.attack_id}-{index:03d}", attack.group, attack.attack_id, index)
        for attack in ATTACKS
        for index in range(1, count + 1)
    ]


def generate_protocol_trials(root: Path, config: dict) -> None:
    candidates = []
    for testbed in config["testbeds"]:
        candidates.extend(_attack_trial_ids(config, testbed))
    injection_ids = [trial_id for trial_id, group, _, _ in candidates if group == "G1"]
    followed = quota_selection(
        injection_ids,
        int(config["injection"]["model_followed"]),
        f"{config['seed']}|injection",
    )
    rows = []
    for trial_id, group, attack_id, index in candidates:
        testbed = trial_id.split("-", 1)[0]
        attempted = trial_id in followed if group == "G1" else True
        trace = evaluate_attack(attack_id, attempted=attempted)
        rows.append(
            {
                "trial_id": trial_id,
                "testbed": testbed,
                "group": group,
                "attack_id": attack_id,
                "attack_family": ATTACK_BY_ID[attack_id].name,
                "trial_index": index,
                "model_followed_attacker_goal": str(attempted).lower() if group == "G1" else "n/a",
                "monitor_decision": trace.monitor_decision,
                "proof_result": trace.proof_result,
                "gateway_decision": trace.gateway_decision,
                "service_effect": str(trace.service_effect).lower(),
                "reject_reason": trace.reject_reason,
                "evidence_class": "manuscript_aligned_reference_projection",
            }
        )
    _write_csv(
        root / "data" / "manuscript_derived" / "causalcred_attack_trials.csv",
        [
            "trial_id",
            "testbed",
            "group",
            "attack_id",
            "attack_family",
            "trial_index",
            "model_followed_attacker_goal",
            "monitor_decision",
            "proof_result",
            "gateway_decision",
            "service_effect",
            "reject_reason",
            "evidence_class",
        ],
        rows,
    )


def generate_baseline_trials(root: Path, config: dict) -> None:
    cloud_ids = _attack_trial_ids(config, "cloud")
    ids_by_group = {
        group: [trial_id for trial_id, candidate_group, _, _ in cloud_ids if candidate_group == group]
        for group in config["attack_groups"]
    }
    rows = []
    for baseline_id, baseline in config["baseline_cloud"].items():
        for group in ("G1", "G2", "G3"):
            cell = baseline[group]
            if not isinstance(cell, dict):
                continue
            selected = quota_selection(
                ids_by_group[group],
                int(cell["successes"]),
                f"{config['seed']}|baseline|{baseline_id}|{group}",
            )
            for trial_id in ids_by_group[group]:
                attack_id = trial_id.split("-")[1]
                effect = trial_id in selected
                rows.append(
                    {
                        "baseline_id": baseline_id,
                        "baseline": baseline["name"],
                        "trial_id": trial_id,
                        "group": group,
                        "attack_id": attack_id,
                        "service_effect": str(effect).lower(),
                        "evidence_class": "deterministic_derivation_from_manuscript_summary",
                    }
                )
    _write_csv(
        root / "data" / "manuscript_derived" / "cloud_baseline_trials.csv",
        ["baseline_id", "baseline", "trial_id", "group", "attack_id", "service_effect", "evidence_class"],
        rows,
    )


def generate_ablation_trials(root: Path, config: dict) -> None:
    base_ids = _attack_trial_ids(config, "cloud")
    rows = []
    representative = {
        "C1": "A7",
        "C2": "A11",
        "C3": "A1",
        "C4": "A3",
        "C5": "A10",
        "C6": "A12",
        "C7": "A13",
    }
    for ablation_id, ablation in config["ablations"].items():
        all_ids = [trial_id for trial_id, _, _, _ in base_ids]
        selected = quota_selection(
            all_ids,
            int(ablation["successes"]),
            f"{config['seed']}|ablation|{ablation_id}",
        )
        removed_control = None if ablation_id == "C0" else Control(ablation_id)
        active_controls = controls_without(removed_control)
        for trial_id, group, attack_id, _ in base_ids:
            exploitable = trial_id in selected
            model_attack = representative.get(ablation_id, attack_id) if exploitable else attack_id
            trace = evaluate_attack(
                model_attack,
                attempted=exploitable,
                active_controls=active_controls,
                violated_control=removed_control if exploitable else None,
            )
            rows.append(
                {
                    "ablation_id": ablation_id,
                    "removed_mechanism": ablation["removed"],
                    "trial_id": trial_id,
                    "group": group,
                    "attack_id": attack_id,
                    "attack_triggered": str(exploitable).lower(),
                    "monitor_decision": trace.monitor_decision,
                    "proof_result": trace.proof_result,
                    "gateway_decision": trace.gateway_decision,
                    "service_effect": str(trace.service_effect).lower(),
                    "evidence_class": "manuscript_aligned_reference_projection",
                }
            )
    _write_csv(
        root / "data" / "manuscript_derived" / "cloud_ablation_trials.csv",
        [
            "ablation_id",
            "removed_mechanism",
            "trial_id",
            "group",
            "attack_id",
            "attack_triggered",
            "monitor_decision",
            "proof_result",
            "gateway_decision",
            "service_effect",
            "evidence_class",
        ],
        rows,
    )


def generate_supply_chain_subset(root: Path, config: dict) -> None:
    trial_ids = [f"digest-{index:03d}" for index in range(1, 251)]
    speranza = quota_selection(
        trial_ids,
        int(config["supply_chain"]["speranza_digest_subset"]["successes"]),
        f"{config['seed']}|speranza",
    )
    rows = []
    for mechanism in ("Speranza-style", "CausalCred"):
        for trial_id in trial_ids:
            effect = trial_id in speranza if mechanism == "Speranza-style" else False
            rows.append(
                {
                    "mechanism": mechanism,
                    "trial_id": trial_id,
                    "service_effect": str(effect).lower(),
                    "predicate": "signed_request" if mechanism == "Speranza-style" else "protected_effect",
                    "evidence_class": "deterministic_derivation_from_manuscript_summary",
                }
            )
    _write_csv(
        root / "data" / "manuscript_derived" / "supply_chain_digest_subset.csv",
        ["mechanism", "trial_id", "service_effect", "predicate", "evidence_class"],
        rows,
    )


def generate_utility_trials(root: Path, config: dict) -> None:
    trials = int(config["utility"]["trials"])
    trial_ids = [f"benign-{index:04d}" for index in range(1, trials + 1)]
    initial_denials = quota_selection(
        trial_ids,
        int(config["utility"]["initial_false_denials"]),
        f"{config['seed']}|utility|initial",
    )
    final_denials = quota_selection(
        trial_ids,
        int(config["utility"]["final_false_denials"]),
        f"{config['seed']}|utility|final",
    )
    rows = [
        {
            "trial_id": trial_id,
            "initial_policy_decision": "deny" if trial_id in initial_denials else "permit",
            "final_policy_decision": "deny" if trial_id in final_denials else "permit",
            "evidence_class": "deterministic_derivation_from_manuscript_summary",
        }
        for trial_id in trial_ids
    ]
    _write_csv(
        root / "data" / "manuscript_derived" / "benign_utility_trials.csv",
        ["trial_id", "initial_policy_decision", "final_policy_decision", "evidence_class"],
        rows,
    )


def generate_correction_trials(root: Path, config: dict) -> None:
    count = int(config["a5_correction"]["trials"])
    trial_ids = [f"a5-{index:03d}" for index in range(1, count + 1)]
    pre_success = quota_selection(
        trial_ids,
        int(config["a5_correction"]["pre_correction_successes"]),
        f"{config['seed']}|a5|pre",
    )
    rows = []
    for version in ("pre_correction", "corrected"):
        for trial_id in trial_ids:
            effect = version == "pre_correction" and trial_id in pre_success
            rows.append(
                {
                    "implementation": version,
                    "trial_id": trial_id,
                    "validator_parent_complete": str(version == "corrected").lower(),
                    "service_effect": str(effect).lower(),
                    "evidence_class": "manuscript_summary_correction_control",
                }
            )
    _write_csv(
        root / "data" / "manuscript_derived" / "a5_correction_trials.csv",
        ["implementation", "trial_id", "validator_parent_complete", "service_effect", "evidence_class"],
        rows,
    )


def generate_privacy_records(root: Path, config: dict) -> None:
    privacy = config["privacy"]
    total = int(privacy["presentations"])
    positives = int(privacy["positive_class"])
    presentation_ids = [f"presentation-{index:05d}" for index in range(1, total + 1)]
    positive_ids = frozenset(presentation_ids[:positives])
    high_unadjusted = quota_selection(
        positive_ids,
        int(privacy["unadjusted_high_signal_positives"]),
        f"{config['seed']}|privacy|unadjusted",
    )
    high_padded = quota_selection(
        positive_ids,
        int(privacy["padded_high_signal_positives"]),
        f"{config['seed']}|privacy|padded",
    )
    buckets = [float(value) for value in privacy["padding_buckets_mib"]]
    overhead = float(privacy["padding_overhead_fraction"])
    rows = []
    for index, presentation_id in enumerate(presentation_ids):
        label = int(presentation_id in positive_ids)
        bucket = buckets[index % len(buckets)]
        original_size = bucket / (1.0 + overhead)
        rows.append(
            {
                "presentation_id": presentation_id,
                "link_label": label,
                "principal_group": f"principal-{index % 200:03d}",
                "task_template": f"template-{index % 40:02d}",
                "timing_class": index % 5,
                "policy_id": f"policy-{index % 16:02d}",
                "epoch_class": index % 4,
                "proof_size_mib": f"{original_size:.9f}",
                "padded_size_mib": f"{bucket:.9f}",
                "link_score_unadjusted": "1" if presentation_id in high_unadjusted else "0",
                "link_score_padded": "1" if presentation_id in high_padded else "0",
                "evidence_class": "deterministic_derivation_from_manuscript_summary",
            }
        )
    _write_csv(
        root / "data" / "manuscript_derived" / "privacy_presentations.csv",
        [
            "presentation_id",
            "link_label",
            "principal_group",
            "task_template",
            "timing_class",
            "policy_id",
            "epoch_class",
            "proof_size_mib",
            "padded_size_mib",
            "link_score_unadjusted",
            "link_score_padded",
            "evidence_class",
        ],
        rows,
    )
    anonymity_rows = [
        {
            "policy_id": f"policy-{index:02d}",
            "eligible_principals": value,
            "rare_clearance_policy": str(value == 1).lower(),
            "evidence_class": "manuscript_summary",
        }
        for index, value in enumerate(privacy["policy_anonymity_sets"], start=1)
    ]
    _write_csv(
        root / "data" / "manuscript_derived" / "policy_anonymity_sets.csv",
        ["policy_id", "eligible_principals", "rare_clearance_policy", "evidence_class"],
        anonymity_rows,
    )


def generate_all(root: Path) -> None:
    config = load_config(root)
    generate_protocol_trials(root, config)
    generate_baseline_trials(root, config)
    generate_ablation_trials(root, config)
    generate_supply_chain_subset(root, config)
    generate_utility_trials(root, config)
    generate_correction_trials(root, config)
    generate_privacy_records(root, config)
