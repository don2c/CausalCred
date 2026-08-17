"""Generate the result-to-artifact index."""

from __future__ import annotations

from pathlib import Path


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_results_index(root: Path) -> None:
    execution_rows = [
        ["E01", "A1-A13 reference execution", "0 protected effects in 6,500 complete-relation trials", "data/executed/trials/*.jsonl", "results/executed/reference_metrics.json: overall", "executed_reference_runtime"],
        ["E02", "C1-C7 paired mutations", "Every single-control removal changes the protected-effect result", "data/executed/control_ablations.jsonl", "results/executed/reference_metrics.json: control_ablations", "executed_reference_runtime"],
        ["E03", "Reference baseline profiles", "Reduced control profiles expose protected effects", "data/executed/baseline_trials.jsonl", "results/executed/reference_metrics.json: reference_baselines", "executed_reference_runtime"],
        ["E04", "Template-clustered analysis", "Deterministic cluster-bootstrap intervals", "data/executed/protocol_trial_index.csv", "results/executed/reference_metrics.json", "executed_reference_runtime"],
        ["E05", "Reference-runtime samples", "10 warm-ups and 100 retained measurements", "results/benchmarks/reference_runtime_samples.csv", "results/benchmarks/reference_runtime_environment.json", "measured_reference_runtime"],
        ["E06", "Source and model identity", "Content-addressed source and explicit deterministic model configuration", "environment/execution_provenance.json", "MANIFEST.sha256", "executed_reference_runtime"],
    ]
    table_rows = []
    descriptions = {
        1: "Approach positioning",
        2: "Core notation",
        3: "Post-quantum profile",
        4: "Cloud baseline UER and Wilson intervals",
        5: "Per-operation cost and memory",
        6: "Cryptographic profile comparison",
        7: "Supply-chain attack results",
        8: "Single-control ablations",
        9: "Compromise and collusion boundaries",
        10: "Trial configuration",
        11: "Instruction decomposition and bound terms",
        12: "Scaling matrix",
        13: "Attack-to-property mapping",
    }
    sources = {
        4: "data/manuscript_derived/cloud_baseline_trials.csv",
        7: "data/manuscript_derived/causalcred_attack_trials.csv; data/manuscript_derived/supply_chain_digest_subset.csv",
        8: "data/manuscript_derived/cloud_ablation_trials.csv",
    }
    for number in range(1, 14):
        source = sources.get(number, "data/reported/manuscript_tables.json")
        table_rows.append(
            [
                f"T{number:02d}",
                f"Table {number}",
                descriptions[number],
                source,
                f"results/tables/table{number:02d}.csv, .md, .tex",
                "make reproduce",
            ]
        )
    result_rows = [
        ["R01", "Abstract; Sections 9.4 and 12", "0/6,500 attacker-directed effects across two testbeds", "data/manuscript_derived/causalcred_attack_trials.csv", "results/metrics.json: security.overall", "reference-model effect predicate and count"],
        ["R02", "Table 4; Section 9.4", "0/3,250 cloud effects; Wilson upper bound 0.12%", "data/manuscript_derived/causalcred_attack_trials.csv", "results/tables/table04.*; results/metrics.json", "Wilson recomputation"],
        ["R03", "Table 7; Section 9.4", "0/3,250 supply-chain effects; Wilson upper bound 0.12%", "data/manuscript_derived/causalcred_attack_trials.csv", "results/tables/table07.*; results/metrics.json", "Wilson recomputation"],
        ["R04", "Section 9.4", "Model followed 1,842/3,000 injected tasks (61.4%)", "data/manuscript_derived/causalcred_attack_trials.csv", "results/metrics.json: injection", "count and rate"],
        ["R05", "Sections 9.4 and 10", "Initial completion 93.8% and false denial 6.17%", "data/manuscript_derived/benign_utility_trials.csv", "results/metrics.json: utility", "count and rate"],
        ["R06", "Abstract; Sections 9.4 and 12", "Final completion 98.2% and false denial 1.83%", "data/manuscript_derived/benign_utility_trials.csv", "results/metrics.json: utility", "count and rate"],
        ["R07", "Section 9.4", "A5 correction changed four admitted effects to zero", "data/manuscript_derived/a5_correction_trials.csv", "results/metrics.json: a5_correction", "before/after count"],
        ["R08", "Section 9.1; Table 11", "208.3 M instructions and component shares", "data/reported/manuscript_tables.json", "results/tables/table11.*; results/metrics.json", "sum and share recomputation"],
        ["R09", "Section 9.1; Table 11", "96-bit ZK term and composed bound below 2^-95.9", "data/reported/manuscript_tables.json", "results/metrics.json: soundness", "union-bound computation"],
        ["R10", "Section 9.1", "168 repetitions: below 2^-118, 5.94 MiB, 0.46 s verification; proving n.m.", "configs/evaluation.json", "results/metrics.json: evidence_boundary", "availability and value check"],
        ["R11", "Section 9.2; Table 5", "8.42 s proving, 0.38 s verification, 4.83 MiB proof, 9.65 s end-to-end", "data/reported/manuscript_tables.json", "results/tables/table05.*; results/metrics.json: cost", "reported-summary preservation"],
        ["R12", "Section 9.2", "Proving 87.3% and transfer 5.3% of latency on 80 Mbit/s path", "data/reported/manuscript_tables.json", "results/metrics.json: cost", "ratio and transfer calculation"],
        ["R13", "Section 9.2", "Observe 2,380/s and head generation 1,640/s", "data/reported/manuscript_tables.json", "results/metrics.json: cost", "latency reciprocal rounded to nearest ten"],
        ["R14", "Section 9.2", "10 Mbit/s proof transfer 4.05 s", "configs/evaluation.json", "results/metrics.json: cost", "size/rate calculation"],
        ["R15", "Section 9.2; Table 5", "Capability profile b=16: 0.92 s amortised", "data/reported/manuscript_tables.json", "results/tables/table05.*", "reported-summary preservation"],
        ["R16", "Section 9.3; Table 12", "Base proving cost 40.4 ms per million instructions", "data/reported/manuscript_tables.json", "results/metrics.json: scaling", "base ratio"],
        ["R17", "Section 9.3; Table 12", "Credential, delegation, and policy range deltas: 5.21, 4.15, 3.43 s", "data/reported/manuscript_tables.json", "results/metrics.json: scaling", "endpoint differences"],
        ["R18", "Section 9.3; Table 12", "10^4 events: 176.5 s and 22.13 MiB", "data/reported/manuscript_tables.json", "results/tables/table12.*; results/metrics.json", "matrix preservation"],
        ["R19", "Section 9.3; Table 12", "Compacted 10^4 events: 11.07 s, 5.54 MiB, 128.3 M state instructions", "data/reported/manuscript_tables.json; configs/evaluation.json", "results/metrics.json: scaling", "matrix and claim check"],
        ["R20", "Section 9.5; Table 8", "Seven ablation UER values", "data/manuscript_derived/cloud_ablation_trials.csv", "results/tables/table08.*", "effect counts and Wilson intervals"],
        ["R21", "Section 9.5", "C2 decomposition: 224 replay plus 96 stale-prefix effects", "configs/evaluation.json", "results/verification.json", "sum check"],
        ["R22", "Section 9.5", "C5 decomposition: 231 substitutions plus 118 fresh-nonce replays", "configs/evaluation.json", "results/verification.json", "sum check"],
        ["R23", "Section 9.6", "40,000 presentations; metadata AUC 0.641", "data/manuscript_derived/privacy_presentations.csv", "results/metrics.json: privacy", "tie-aware ROC AUC"],
        ["R24", "Section 9.6", "Padded AUC 0.512 with 14.6% mean overhead", "data/manuscript_derived/privacy_presentations.csv", "results/metrics.json: privacy", "ROC AUC and mean overhead"],
        ["R25", "Section 9.6", "16 policies; median anonymity set 1,842; three at most four; minimum one", "data/manuscript_derived/policy_anonymity_sets.csv", "results/metrics.json: privacy", "median and threshold counts"],
    ]
    lines = [
        "# Result and artifact index",
        "",
        "All paths are relative to the repository root. Executed evidence and manuscript-summary evidence are indexed independently.",
        "",
        "## Executed reference results",
        "",
        "| ID | Experiment | Result | Source evidence | Output | Evidence class |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend("| " + " | ".join(_escape(value) for value in row) + " |" for row in execution_rows)
    lines.extend([
        "",
        "## Manuscript-summary tables",
        "",
        "| ID | Manuscript location | Content | Source data | Regenerated output | Procedure |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    lines.extend("| " + " | ".join(_escape(value) for value in row) + " |" for row in table_rows)
    lines.extend(
        [
            "",
            "## Manuscript-summary arithmetic",
            "",
            "| ID | Manuscript location | Result | Source data | Output | Validation |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend("| " + " | ".join(_escape(value) for value in row) + " |" for row in result_rows)
    lines.extend(
        [
            "",
            "## Evidence-status rule",
            "",
            "Executed reference records are generated exclusively by the protocol runtime. Manuscript-summary values and deterministic derivations remain in separate paths and carry distinct `evidence_class` values.",
            "",
        ]
    )
    (root / "RESULTS_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
