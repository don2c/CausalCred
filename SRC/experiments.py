"""End-to-end reference experiments and evidence generation."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .model import ALL_CONTROLS, ATTACKS, Control, controls_without
from .protocol import build_scenario, evaluate_scenario, trace_record
from .stats import clustered_bootstrap_mean_interval, rate_ci_percent, wilson_interval


BASELINE_CONTROLS = {
    "R0-workload-abac": frozenset(),
    "R1-stateful-auth": frozenset({Control.NONCE_FRESH_HEAD, Control.CURRENT_REVOCATION}),
    "R2-anonymous-credential": frozenset({Control.ROOT_BINDING, Control.SUITE_BINDING}),
    "R3-agent-governance": frozenset({Control.ROOT_BINDING, Control.CURRENT_REVOCATION}),
    "R4-signed-request": frozenset(
        {Control.NONCE_FRESH_HEAD, Control.EXACT_ACTION_BINDING, Control.SUITE_BINDING}
    ),
    "R5-causalcred-reference": ALL_CONTROLS,
}


ABLATION_ATTACK = {
    Control.ROOT_BINDING: "A7",
    Control.NONCE_FRESH_HEAD: "A11",
    Control.INTEGRITY_PROPAGATION: "A1",
    Control.ENDORSEMENT_CHECKING: "A3",
    Control.EXACT_ACTION_BINDING: "A10",
    Control.CURRENT_REVOCATION: "A12",
    Control.SUITE_BINDING: "A13",
}


def _load_config(root: Path) -> dict:
    return json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))


def _selected(seed: str, trial_id: str, probability: float) -> bool:
    value = int(hashlib.sha256(f"{seed}|{trial_id}".encode("utf-8")).hexdigest()[:16], 16)
    return value / float(0xFFFFFFFFFFFFFFFF) < probability


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _source_revision(root: Path) -> dict:
    included_roots = [
        root / "src",
        root / "tests",
        root / "scripts",
        root / "configs",
        root / "docs",
        root / "schemas",
        root / ".github",
    ]
    included_files = [
        root / "README.md",
        root / "ARTIFACT.md",
        root / "Makefile",
        root / "Dockerfile",
        root / "pyproject.toml",
        root / "LICENSE",
    ]
    paths = [path for start in included_roots for path in start.rglob("*") if path.is_file()]
    paths.extend(path for path in included_files if path.is_file())
    paths = sorted(
        path
        for path in paths
        if "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pdf"}
    )
    digest = hashlib.sha256()
    entries = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": relative, "sha256": file_digest})
        digest.update(f"{file_digest}  {relative}\n".encode("utf-8"))
    return {
        "algorithm": "sha256",
        "source_revision_sha256": digest.hexdigest(),
        "source_file_count": len(entries),
        "files": entries,
    }


def run_reference_evaluation(root: Path) -> dict:
    """Execute the reference runtime and emit complete per-trial evidence."""
    config = _load_config(root)
    execution = config["reference_execution"]
    trial_count = int(execution["trials_per_family_per_testbed"])
    attempt_probability = float(execution["injection_attempt_probability"])
    seed = str(execution["seed"])
    testbeds = tuple(execution["testbeds"])

    records = []
    compact_rows = []
    for testbed in testbeds:
        for attack in ATTACKS:
            for index in range(1, trial_count + 1):
                trial_id = f"{testbed}-{attack.attack_id}-{index:03d}"
                selected = attack.group != "G1" or _selected(seed, trial_id, attempt_probability)
                scenario = build_scenario(
                    testbed,
                    attack.attack_id,
                    trial_id,
                    attacker_goal_selected=selected,
                )
                trace = evaluate_scenario(scenario)
                template_id = f"{testbed}-{attack.attack_id}-template-{(index - 1) % 25:02d}"
                record = trace_record(scenario, trace)
                record["trial"]["group"] = attack.group
                record["trial"]["template_id"] = template_id
                record["model"] = {
                    "provider": "local-deterministic",
                    "identifier": execution["model_identifier"],
                    "decoding": execution["decoding"],
                }
                records.append(record)
                compact_rows.append(
                    {
                        "trial_id": trial_id,
                        "testbed": testbed,
                        "group": attack.group,
                        "attack_id": attack.attack_id,
                        "template_id": template_id,
                        "attacker_goal_selected": str(selected).lower(),
                        "monitor_decision": trace.monitor_decision,
                        "relation_decision": trace.relation_decision,
                        "gateway_decision": trace.gateway_decision,
                        "service_effect": str(trace.service_effect).lower(),
                        "reject_reason": trace.reject_reason,
                        "statement_digest": trace.statement_digest,
                        "evidence_class": "executed_reference_runtime",
                    }
                )

    executed_dir = root / "data" / "executed"
    records_by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        trial = record["trial"]
        records_by_cell[(trial["testbed"], trial["attack_id"])].append(record)
    trials_dir = executed_dir / "trials"
    trials_dir.mkdir(parents=True, exist_ok=True)
    for key, cell_records in sorted(records_by_cell.items()):
        _write_jsonl(trials_dir / f"{key[0]}-{key[1]}.jsonl", cell_records)
    with (executed_dir / "protocol_trial_index.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(compact_rows[0]))
        writer.writeheader()
        writer.writerows(compact_rows)

    ablation_records = []
    for testbed in testbeds:
        for control, attack_id in ABLATION_ATTACK.items():
            for index in range(1, trial_count + 1):
                trial_id = f"{testbed}-{control.value}-{index:03d}"
                scenario = build_scenario(
                    testbed,
                    attack_id,
                    trial_id,
                    target_control=control,
                )
                full = evaluate_scenario(scenario)
                removed = evaluate_scenario(scenario, active_controls=controls_without(control))
                ablation_records.append(
                    {
                        "schema_version": 1,
                        "trial_id": trial_id,
                        "testbed": testbed,
                        "attack_id": attack_id,
                        "removed_control": control.value,
                        "full_service_effect": full.service_effect,
                        "ablated_service_effect": removed.service_effect,
                        "full_reject_reason": full.reject_reason,
                        "ablated_gateway_decision": removed.gateway_decision,
                        "scenario_digest": full.statement_digest,
                        "evidence_class": "executed_reference_runtime",
                    }
                )
    _write_jsonl(executed_dir / "control_ablations.jsonl", ablation_records)

    baseline_records = []
    for compact in compact_rows:
        scenario = build_scenario(
            compact["testbed"],
            compact["attack_id"],
            compact["trial_id"],
            attacker_goal_selected=compact["attacker_goal_selected"] == "true",
        )
        for profile, controls in BASELINE_CONTROLS.items():
            trace = evaluate_scenario(scenario, active_controls=controls)
            baseline_records.append(
                {
                    "trial_id": compact["trial_id"],
                    "testbed": compact["testbed"],
                    "group": compact["group"],
                    "attack_id": compact["attack_id"],
                    "profile": profile,
                    "active_controls": sorted(control.value for control in controls),
                    "service_effect": trace.service_effect,
                    "gateway_decision": trace.gateway_decision,
                    "evidence_class": "executed_reference_runtime",
                }
            )
    _write_jsonl(executed_dir / "baseline_trials.jsonl", baseline_records)

    summary = _summarise_reference(compact_rows, ablation_records, baseline_records, execution)
    _write_json(root / "results" / "executed" / "reference_metrics.json", summary)

    provenance = {
        "schema_version": 1,
        "artifact_scope": "executable Causal-ABAC reference evaluation",
        "source": _source_revision(root),
        "execution": {
            "provider": "local-deterministic",
            "model_identifier": execution["model_identifier"],
            "decoding": execution["decoding"],
            "seed": seed,
            "testbeds": list(testbeds),
            "trials_per_family_per_testbed": trial_count,
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    }
    _write_json(root / "environment" / "execution_provenance.json", provenance)
    return summary


def _summarise_reference(
    rows: list[dict],
    ablations: list[dict],
    baselines: list[dict],
    execution: dict,
) -> dict:
    effects = [1.0 if row["service_effect"] == "true" else 0.0 for row in rows]
    clusters = [row["template_id"] for row in rows]
    overall_successes = int(sum(effects))
    lower, upper = wilson_interval(overall_successes, len(rows))
    bootstrap = clustered_bootstrap_mean_interval(
        effects,
        clusters,
        iterations=int(execution["bootstrap_iterations"]),
        seed=f"{execution['seed']}|effects",
    )
    selected_rows = [row for row in rows if row["group"] == "G1"]
    selected_values = [
        1.0 if row["attacker_goal_selected"] == "true" else 0.0 for row in selected_rows
    ]
    selected_clusters = [row["template_id"] for row in selected_rows]
    selected_bootstrap = clustered_bootstrap_mean_interval(
        selected_values,
        selected_clusters,
        iterations=int(execution["bootstrap_iterations"]),
        seed=f"{execution['seed']}|selected",
    )

    groups = {}
    for key in sorted({(row["testbed"], row["group"]) for row in rows}):
        subset = [row for row in rows if (row["testbed"], row["group"]) == key]
        successes = sum(row["service_effect"] == "true" for row in subset)
        groups["/".join(key)] = {
            "successes": successes,
            "trials": len(subset),
            "uer_wilson_95_percent": rate_ci_percent(successes, len(subset)),
        }

    ablation_summary = {}
    for control in sorted(control.value for control in Control):
        subset = [row for row in ablations if row["removed_control"] == control]
        ablation_summary[control] = {
            "full_effects": sum(row["full_service_effect"] for row in subset),
            "ablated_effects": sum(row["ablated_service_effect"] for row in subset),
            "trials": len(subset),
        }

    baseline_summary = {}
    for profile in BASELINE_CONTROLS:
        subset = [row for row in baselines if row["profile"] == profile]
        successes = sum(row["service_effect"] for row in subset)
        baseline_summary[profile] = {
            "successes": successes,
            "trials": len(subset),
            "uer_wilson_95_percent": rate_ci_percent(successes, len(subset)),
        }

    return {
        "schema_version": 1,
        "evidence_class": "executed_reference_runtime",
        "overall": {
            "successes": overall_successes,
            "trials": len(rows),
            "uer_percent": 100.0 * overall_successes / len(rows),
            "wilson_95_percent": [100.0 * lower, 100.0 * upper],
            "template_clustered_bootstrap_95_percent": [
                100.0 * bootstrap[0],
                100.0 * bootstrap[1],
            ],
        },
        "attacker_goal_selection": {
            "selected": int(sum(selected_values)),
            "trials": len(selected_values),
            "rate_percent": 100.0 * sum(selected_values) / len(selected_values),
            "template_clustered_bootstrap_95_percent": [
                100.0 * selected_bootstrap[0],
                100.0 * selected_bootstrap[1],
            ],
        },
        "groups": groups,
        "control_ablations": ablation_summary,
        "reference_baselines": baseline_summary,
    }


def benchmark_reference_runtime(
    root: Path,
    *,
    warmups: int = 10,
    measured_runs: int = 100,
) -> Path:
    """Record sample-level timings for the executable reference runtime."""
    scenario = build_scenario("cloud", "A10", "benchmark-reference")
    for _ in range(warmups):
        evaluate_scenario(scenario)
    output = root / "results" / "benchmarks" / "reference_runtime_samples.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(1, measured_runs + 1):
        start = time.perf_counter_ns()
        trace = evaluate_scenario(scenario)
        elapsed = time.perf_counter_ns() - start
        rows.append(
            {
                "sample": index,
                "operation": "evaluate_reference_authorisation",
                "elapsed_ns": elapsed,
                "gateway_decision": trace.gateway_decision,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "evidence_class": "measured_reference_runtime",
            }
        )
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "schema_version": 1,
        "operation": "evaluate_reference_authorisation",
        "warmups": warmups,
        "measured_runs": measured_runs,
        "timer": "time.perf_counter_ns",
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "evidence_class": "measured_reference_runtime",
    }
    _write_json(root / "results" / "benchmarks" / "reference_runtime_environment.json", metadata)
    return output
