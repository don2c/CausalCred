"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .experiments import benchmark_reference_runtime, run_reference_evaluation
from .generate import generate_all
from .index import write_results_index
from .metrics import compute_metrics
from .tables import generate_tables
from .verify import verify_all, write_manifest


def reproduce(root: Path) -> None:
    run_reference_evaluation(root)
    generate_all(root)
    generate_tables(root)
    compute_metrics(root)
    write_results_index(root)
    report = verify_all(root)
    write_manifest(root)
    print(f"reproduction: {report['checks_passed']} checks passed")


def verify(root: Path) -> None:
    report = verify_all(root)
    write_manifest(root)
    print(f"verification: {report['status']}")


def benchmark(root: Path) -> None:
    output = benchmark_reference_runtime(root)
    print(f"benchmark samples: {output.relative_to(root)}")


def clean(root: Path) -> None:
    generated_files = [
        root / "RESULTS_INDEX.md",
        root / "MANIFEST.sha256",
        root / "results" / "metrics.json",
        root / "results" / "verification.json",
        root / "results" / "TABLES.md",
        root / "results" / "executed" / "reference_metrics.json",
        root / "environment" / "execution_provenance.json",
    ]
    generated_files.extend(
        path for path in (root / "data" / "executed").rglob("*") if path.is_file()
    )
    generated_files.extend((root / "data" / "manuscript_derived").glob("*.csv"))
    generated_files.extend((root / "results" / "tables").glob("table*.*"))
    for path in generated_files:
        if path.is_file():
            path.unlink()
    print("generated evaluation outputs removed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CausalCred evaluation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("reproduce", "verify", "benchmark", "clean"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "reproduce":
        reproduce(root)
    elif args.command == "verify":
        verify(root)
    elif args.command == "benchmark":
        benchmark(root)
    else:
        clean(root)
    return 0
