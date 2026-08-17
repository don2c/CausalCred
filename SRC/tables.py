"""Regenerate manuscript tables in CSV, Markdown, and LaTeX formats."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .stats import rate_ci_percent


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _count_effects(rows: list[dict[str, str]]) -> tuple[int, int]:
    return sum(row["service_effect"] == "true" for row in rows), len(rows)


def _cell(successes: int, trials: int) -> str:
    return f"{successes}/{trials}; {rate_ci_percent(successes, trials)}"


def _markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(character, character) for character in text)


def _write_table(root: Path, number: int, table: dict) -> None:
    output = root / "results" / "tables"
    output.mkdir(parents=True, exist_ok=True)
    stem = output / f"table{number:02d}"
    columns = table["columns"]
    rows = table["rows"]
    with stem.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    markdown = [f"# Table {number}: {table['title']}", ""]
    markdown.append("| " + " | ".join(_markdown_escape(column) for column in columns) + " |")
    markdown.append("| " + " | ".join("---" for _ in columns) + " |")
    markdown.extend(
        "| " + " | ".join(_markdown_escape(value) for value in row) + " |" for row in rows
    )
    markdown.append("")
    stem.with_suffix(".md").write_text("\n".join(markdown), encoding="utf-8")
    alignment = "l" * len(columns)
    latex = [
        r"\begin{table*}[t]",
        r"\centering",
        rf"\caption{{{_latex_escape(table['title'])}}}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\hline",
        " & ".join(_latex_escape(column) for column in columns) + r" \\",
        r"\hline",
    ]
    latex.extend(" & ".join(_latex_escape(value) for value in row) + r" \\" for row in rows)
    latex.extend([r"\hline", r"\end{tabular}", r"\end{table*}", ""])
    stem.with_suffix(".tex").write_text("\n".join(latex), encoding="utf-8")


def _table4(root: Path, config: dict) -> dict:
    records = _read_csv(root / "data" / "manuscript_derived" / "cloud_baseline_trials.csv")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in records:
        grouped[(row["baseline_id"], row["group"])].append(row)
    rows = []
    for baseline_id, baseline in config["baseline_cloud"].items():
        output = [baseline_id, baseline["name"]]
        aggregate_successes = 0
        aggregate_trials = 0
        measured = False
        for group in ("G1", "G2", "G3"):
            specification = baseline[group]
            if isinstance(specification, dict):
                successes, trials = _count_effects(grouped[(baseline_id, group)])
                output.append(_cell(successes, trials))
                aggregate_successes += successes
                aggregate_trials += trials
                measured = True
            else:
                output.append(specification)
        if measured:
            output.append(_cell(aggregate_successes, aggregate_trials))
        else:
            output.append("n.m.")
        rows.append(output)
    return {
        "title": "Cloud-testbed uncontrolled-effect rate (UER), Wilson 95% intervals",
        "columns": ["ID", "Baseline", "G1 (n=1,500)", "G2 (n=750)", "G3 (n=1,000)", "In-scope aggregate"],
        "rows": rows,
    }


def _table7(root: Path) -> dict:
    attack_records = [
        row
        for row in _read_csv(root / "data" / "manuscript_derived" / "causalcred_attack_trials.csv")
        if row["testbed"] == "supply_chain"
    ]
    subset = _read_csv(root / "data" / "manuscript_derived" / "supply_chain_digest_subset.csv")
    rows = []
    for group, label in (("G1", "G1 (A1-A6)"), ("G2", "G2 (A7-A9)"), ("G3", "G3 (A10-A13)")):
        successes, trials = _count_effects([row for row in attack_records if row["group"] == group])
        rows.append(["CausalCred", label, f"{successes}/{trials}", rate_ci_percent(successes, trials)])
    successes, trials = _count_effects(attack_records)
    rows.append(["CausalCred", "All A1-A13", f"{successes}/{trials}", rate_ci_percent(successes, trials)])
    for mechanism, label in (("Speranza-style", "Digest subset*"), ("CausalCred", "Same subset")):
        selected = [row for row in subset if row["mechanism"] == mechanism]
        successes, trials = _count_effects(selected)
        rows.append([mechanism, label, f"{successes}/{trials}", rate_ci_percent(successes, trials)])
    return {
        "title": "Software-supply-chain attack results",
        "columns": ["Mechanism", "Trial set", "Observed/trials", "Rate [95% CI] (%)"],
        "rows": rows,
    }


def _table8(root: Path, config: dict) -> dict:
    records = _read_csv(root / "data" / "manuscript_derived" / "cloud_ablation_trials.csv")
    rows = []
    for ablation_id, ablation in config["ablations"].items():
        selected = [row for row in records if row["ablation_id"] == ablation_id]
        successes, trials = _count_effects(selected)
        rows.append(
            [
                ablation_id,
                ablation["removed"],
                f"{successes}/{trials}",
                rate_ci_percent(successes, trials),
            ]
        )
    return {
        "title": "Cloud-testbed single-control ablations (3,250 trials each)",
        "columns": ["ID", "Removed mechanism", "Success/trials", "UER [95% CI] (%)"],
        "rows": rows,
    }


def generate_tables(root: Path) -> dict[int, dict]:
    config = json.loads((root / "configs" / "evaluation.json").read_text(encoding="utf-8"))
    source = json.loads(
        (root / "data" / "reported" / "manuscript_tables.json").read_text(encoding="utf-8")
    )
    tables = {
        1: source["table1"],
        2: source["table2"],
        3: source["table3"],
        4: _table4(root, config),
        5: source["table5"],
        6: source["table6"],
        7: _table7(root),
        8: _table8(root, config),
        9: source["table9"],
        10: source["table10"],
        11: source["table11"],
        12: source["table12"],
        13: source["table13"],
    }
    for number, table in tables.items():
        _write_table(root, number, table)
    combined = ["# Regenerated manuscript tables", ""]
    for number in range(1, 14):
        combined.append((root / "results" / "tables" / f"table{number:02d}.md").read_text(encoding="utf-8"))
    (root / "results" / "TABLES.md").write_text("\n".join(combined), encoding="utf-8")
    return tables
