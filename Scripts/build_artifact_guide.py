#!/usr/bin/env python3
"""Build the standalone CausalCred artifact evaluation guide."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#245A8D")
CYAN = colors.HexColor("#DCEEF8")
GREEN = colors.HexColor("#DDEFE3")
GOLD = colors.HexColor("#F4E8C1")
LIGHT = colors.HexColor("#F4F6F8")
MID = colors.HexColor("#CBD5DF")
DARK = colors.HexColor("#263238")
MUTED = colors.HexColor("#5B6770")


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _table(data: list[list[object]], widths: list[float], header: bool = True) -> Table:
    formatted = []
    for row_index, row in enumerate(data):
        style_name = "TableHeader" if header and row_index == 0 else "TableBody"
        formatted.append([Paragraph(str(value), STYLES[style_name]) for value in row])
    table = Table(formatted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, MID),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    table.setStyle(TableStyle(commands))
    return table


def _callout(title: str, body: str, background=CYAN) -> Table:
    content = [
        [Paragraph(title, STYLES["CalloutTitle"])],
        [Paragraph(body, STYLES["CalloutBody"])],
    ]
    table = Table(content, colWidths=[7.15 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.8, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    return table


def _page(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 0.34 * inch, width, 0.34 * inch, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(0.65 * inch, height - 0.22 * inch, "CAUSALCRED ARTIFACT EVALUATION GUIDE")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.65 * inch, 0.35 * inch, "Executable reference evaluation and evidence specification")
    canvas.drawRightString(width - 0.65 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build(root: Path, output: Path) -> None:
    metrics = json.loads(
        (root / "results" / "executed" / "reference_metrics.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(
        (root / "environment" / "execution_provenance.json").read_text(encoding="utf-8")
    )
    revision = provenance["source"]["source_revision_sha256"]
    overall = metrics["overall"]
    selection = metrics["attacker_goal_selection"]

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.62 * inch,
        title="CausalCred Artifact Evaluation Guide",
        author="CausalCred artifact authors",
        subject="Executable reference evaluation and reviewer instructions",
    )

    story = [
        Spacer(1, 0.20 * inch),
        Paragraph("CausalCred", STYLES["Title"]),
        Paragraph("Artifact Evaluation Guide", STYLES["Subtitle"]),
        Spacer(1, 0.12 * inch),
        Paragraph(
            "Executable protocol-state evaluation, evidence provenance, mutation analysis, "
            "and manuscript-consistency workflow",
            STYLES["Lead"],
        ),
        Spacer(1, 0.25 * inch),
        _callout(
            "Reference execution result",
            f"The complete relation produced <b>{overall['successes']}/{overall['trials']}</b> "
            f"protected attacker effects. The two-sided Wilson 95% upper bound is "
            f"<b>{overall['wilson_95_percent'][1]:.3f}%</b>. Every paired C1-C7 removal "
            "changed the corresponding protected-effect decision.",
            GREEN,
        ),
        Spacer(1, 0.18 * inch),
        _table(
            [
                ["Package property", "Registered value"],
                ["Execution provider", provenance["execution"]["provider"]],
                ["Model identifier", provenance["execution"]["model_identifier"]],
                ["Sampling", "Disabled, temperature 0, top-p 1"],
                ["Trial allocation", "250 per A1-A13 family in each of two testbeds"],
                ["Source revision", revision],
                ["Primary command", "make verify"],
            ],
            [1.75 * inch, 5.40 * inch],
        ),
        Spacer(1, 0.20 * inch),
        Paragraph("Purpose", STYLES["H1"]),
        Paragraph(
            "This guide defines the evidence classes, reviewer procedure, protocol-runtime "
            "invariants, statistical methods, and interpretation boundaries of the CausalCred "
            "evaluation package. The package separates executed protocol evidence from "
            "manuscript-summary arithmetic at the directory and record levels.",
            STYLES["Body"],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("1. Evidence architecture", STYLES["H1"]),
        Paragraph(
            "Four evidence classes prevent measurements, executions, and manuscript summaries "
            "from being conflated. Each generated row or object carries an evidence_class field.",
            STYLES["Body"],
        ),
        Spacer(1, 0.10 * inch),
        _table(
            [
                ["Evidence class", "Definition", "Location"],
                ["executed_reference_runtime", "Concrete protocol-state execution", "data/executed/"],
                ["measured_reference_runtime", "Retained local timing samples", "results/benchmarks/"],
                ["manuscript_summary", "Value transcribed from the manuscript", "data/reported/"],
                [
                    "deterministic_derivation_from_manuscript_summary",
                    "Arithmetic or row projection from summary inputs",
                    "data/manuscript_derived/",
                ],
            ],
            [2.25 * inch, 3.10 * inch, 1.80 * inch],
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Executed state", STYLES["H2"]),
        Paragraph(
            "Every reference trial records compound-principal roots, credentials, an attenuating "
            "delegation edge, monitor events, declared model context, provenance parents, integrity "
            "labels, challenge epochs, request digests, proof-state decisions, gateway decisions, "
            "and the protected-service effect.",
            STYLES["Body"],
        ),
        Paragraph("Cryptographic interpretation", STYLES["H2"]),
        Paragraph(
            "Domain-separated SHA-256 commitments provide stable state identifiers in the reference "
            "runtime. Runtime timing characterizes the executable specification. It does not estimate "
            "Ligetron, ML-DSA, ML-KEM, attestation, or production network performance.",
            STYLES["Body"],
        ),
        Paragraph("Source identity", STYLES["H2"]),
        Paragraph(
            "The provenance record hashes every source, configuration, schema, test, script, "
            "documentation, and build file that defines the execution. The release manifest hashes "
            "all distributed files except the manifest itself.",
            STYLES["Body"],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("2. Reviewer procedure", STYLES["H1"]),
        _callout(
            "Primary command",
            "Run <font name='Courier-Bold'>make verify</font> from the package root. "
            "The final line must be <font name='Courier-Bold'>verification: PASS</font>.",
            CYAN,
        ),
        Spacer(1, 0.15 * inch),
        _table(
            [
                ["Stage", "Operation", "Expected evidence"],
                ["1", "Execute A1-A13 in both testbeds", "6,500 complete JSONL records"],
                ["2", "Execute paired C1-C7 mutations", "3,500 full and removed-control pairs"],
                ["3", "Execute six control profiles", "39,000 baseline-profile decisions"],
                ["4", "Compute intervals and aggregates", "Wilson and clustered-bootstrap outputs"],
                ["5", "Regenerate manuscript tables", "13 tables in CSV, Markdown, and LaTeX"],
                ["6", "Run tests and invariant checks", "17 tests and 114 registered checks"],
                ["7", "Write integrity manifest", "SHA-256 digest for every release file"],
            ],
            [0.55 * inch, 3.05 * inch, 3.55 * inch],
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Clean-room execution", STYLES["H2"]),
        Paragraph("make clean<br/>make verify", STYLES["Code"]),
        Paragraph(
            "The clean target removes generated trial, table, metric, index, provenance, and "
            "manifest outputs. Benchmark samples are retained as measurement evidence. Use "
            "make benchmark to collect a new set of 100 measurements after 10 warm-ups.",
            STYLES["Body"],
        ),
        Paragraph("Container execution", STYLES["H2"]),
        Paragraph(
            "docker build -t causalcred-artifact .<br/>docker run --rm causalcred-artifact",
            STYLES["Code"],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("3. Executed claims and acceptance conditions", STYLES["H1"]),
        _table(
            [
                ["ID", "Executed claim", "Acceptance condition"],
                ["E1", "Complete relation blocks A1-A13", "0 effects in 6,500 trials"],
                ["E2", "Each control is outcome-relevant", "Every C1-C7 paired removal permits"],
                ["E3", "Reduced profiles expose effects", "R5 has zero and weaker profiles are nonzero"],
                ["E4", "Exact request is gateway-bound", "A10 proof valid, gateway rejects substitution"],
                ["E5", "Model context is parent-complete", "A5 rejected before proof construction"],
                ["E6", "Allocation and source are immutable", "26 x 250 cells and valid SHA-256 digests"],
            ],
            [0.50 * inch, 3.25 * inch, 3.40 * inch],
        ),
        Spacer(1, 0.16 * inch),
        _callout(
            "Goal-selection stress",
            f"The deterministic agent selected the attacker goal in <b>{selection['selected']}/"
            f"{selection['trials']}</b> G1 trials ({selection['rate_percent']:.2f}%). "
            f"The template-clustered 95% interval is "
            f"[{selection['template_clustered_bootstrap_95_percent'][0]:.2f}%, "
            f"{selection['template_clustered_bootstrap_95_percent'][1]:.2f}%].",
            GOLD,
        ),
        Spacer(1, 0.17 * inch),
        Paragraph("Reference baseline outcomes", STYLES["H2"]),
        _table(
            [["Profile", "Effects/trials", "UER with Wilson 95% CI"]]
            + [
                [
                    profile,
                    f"{entry['successes']}/{entry['trials']}",
                    entry["uer_wilson_95_percent"],
                ]
                for profile, entry in metrics["reference_baselines"].items()
            ],
            [2.65 * inch, 1.45 * inch, 3.05 * inch],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("4. Protocol control analysis", STYLES["H1"]),
        _table(
            [
                ["Control", "Invariant", "Concrete violating state"],
                ["C1", "Compound root and delegation binding", "Foreign root, equal approver root, or widened operation"],
                ["C2", "Nonce-fresh monitor head", "Previously consumed challenge nonce"],
                ["C3", "Integrity and parent propagation", "Low-integrity parent, omitted context, or future parent"],
                ["C4", "Endorsement validity", "Required transformation with invalid endorsement"],
                ["C5", "Exact-action binding", "Forwarded request differs from proof-bound request"],
                ["C6", "Current revocation and epochs", "Stale epoch and revoked agent root"],
                ["C7", "Suite binding", "Challenge names a downgraded suite"],
            ],
            [0.55 * inch, 2.70 * inch, 3.90 * inch],
        ),
        Spacer(1, 0.16 * inch),
        Paragraph("Mutation-test requirement", STYLES["H2"]),
        Paragraph(
            "Each control receives a scenario that violates only that control. The test executes "
            "identical state with the complete relation and with one control removed. Acceptance "
            "requires rejection in the first execution and a protected effect in the second. This "
            "test detects an implementation that returns outcomes from attack identifiers alone.",
            STYLES["Body"],
        ),
        Paragraph("Per-stage observability", STYLES["H2"]),
        Paragraph(
            "A10 demonstrates a valid proof followed by gateway rejection because request digests "
            "differ. A5 demonstrates monitor rejection before proof construction because declared "
            "model context is not parent-complete. The JSONL traces expose both sequences directly.",
            STYLES["Body"],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("5. Statistics, measurements, and interpretation", STYLES["H1"]),
        _table(
            [
                ["Procedure", "Implementation rule"],
                ["UER interval", "Two-sided Wilson interval, z = 1.96"],
                ["Clustered interval", "Resample complete template clusters, 2,000 iterations"],
                ["AUC", "Mann-Whitney statistic with half credit for ties"],
                ["Padding overhead", "Arithmetic mean of padded/original minus one"],
                ["Security composition", "Multiplicity-weighted union bound"],
                ["Runtime measurement", "10 warm-ups, 100 retained perf_counter_ns samples"],
            ],
            [2.20 * inch, 4.95 * inch],
        ),
        Spacer(1, 0.16 * inch),
        Paragraph("Cluster dependence", STYLES["H2"]),
        Paragraph(
            "Trials share task templates. The bootstrap samples whole template clusters with "
            "replacement so that within-template observations remain grouped. A deterministic seed "
            "makes the interval exactly reproducible. Unit tests validate deterministic output and "
            "coverage of the observed mean.",
            STYLES["Body"],
        ),
        Paragraph("Measurement boundary", STYLES["H2"]),
        Paragraph(
            "Sample-level timings in this package are measurements of the Python reference runtime. "
            "Manuscript cryptographic and system-performance values remain manuscript-summary "
            "records. Their arithmetic can be checked, while the reference benchmark must be "
            "interpreted under its recorded environment and operation name.",
            STYLES["Body"],
        ),
        Paragraph("Overall zero-success interval", STYLES["H2"]),
        Paragraph(
            f"For {overall['successes']} successes in {overall['trials']} trials, the Wilson 95% "
            f"interval is [{overall['wilson_95_percent'][0]:.3f}%, "
            f"{overall['wilson_95_percent'][1]:.3f}%]. The clustered-bootstrap interval is "
            f"[{overall['template_clustered_bootstrap_95_percent'][0]:.3f}%, "
            f"{overall['template_clustered_bootstrap_95_percent'][1]:.3f}%].",
            STYLES["Body"],
        ),
        PageBreak(),
        Spacer(1, 0.18 * inch),
        Paragraph("6. File map and reviewer checklist", STYLES["H1"]),
        _table(
            [
                ["Path", "Reviewer purpose"],
                ["src/causalcred_eval/protocol.py", "Inspect concrete state and verification logic"],
                ["src/causalcred_eval/experiments.py", "Inspect allocation, execution, bootstrap, and provenance"],
                ["data/executed/trials/*.jsonl", "Audit complete per-trial evidence"],
                ["data/executed/control_ablations.jsonl", "Audit paired control mutations"],
                ["results/executed/reference_metrics.json", "Inspect executed aggregates and intervals"],
                ["environment/execution_provenance.json", "Verify model, configuration, source, and runtime identity"],
                ["schemas/", "Inspect machine-readable evidence contracts"],
                ["RESULTS_INDEX.md", "Resolve claims to evidence and output files"],
                ["MANIFEST.sha256", "Validate release integrity"],
            ],
            [3.00 * inch, 4.15 * inch],
        ),
        Spacer(1, 0.17 * inch),
        Paragraph("Acceptance checklist", STYLES["H2"]),
        _table(
            [
                ["Check", "Required result"],
                ["Clean execution", "make verify exits successfully"],
                ["Complete relation", "0 protected effects in executed reference trials"],
                ["Mutation sensitivity", "Every C1-C7 removal changes its paired outcome"],
                ["Evidence identity", "All executed records have the expected evidence class"],
                ["Allocation", "250 trials for each attack and testbed cell"],
                ["Statistics", "Wilson and clustered-bootstrap checks pass"],
                ["Measurements", "100 positive sample-level timing observations are retained"],
                ["Integrity", "sha256sum -c MANIFEST.sha256 reports no failure"],
            ],
            [2.20 * inch, 4.95 * inch],
        ),
        Spacer(1, 0.16 * inch),
        _callout(
            "Interpretation rule",
            "Executed reference evidence supports protocol-state and control-flow claims. "
            "Manuscript-summary evidence supports transcription and arithmetic checks. "
            "Reference-runtime timing supports only the named local operation.",
            CYAN,
        ),
    ]

    document.build(story, onFirstPage=_page, onLaterPages=_page)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("docs/CausalCred_Artifact_Guide.pdf"))
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
    return 0


SAMPLE = getSampleStyleSheet()
STYLES = {
    "Title": ParagraphStyle(
        "Title",
        parent=SAMPLE["Title"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=31,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=2,
    ),
    "Subtitle": ParagraphStyle(
        "Subtitle",
        parent=SAMPLE["Heading2"],
        fontName="Helvetica",
        fontSize=17,
        leading=21,
        textColor=BLUE,
        alignment=TA_LEFT,
    ),
    "Lead": ParagraphStyle(
        "Lead",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=DARK,
    ),
    "H1": ParagraphStyle(
        "H1",
        parent=SAMPLE["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=NAVY,
        spaceBefore=4,
        spaceAfter=9,
        keepWithNext=True,
    ),
    "H2": ParagraphStyle(
        "H2",
        parent=SAMPLE["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    ),
    "Body": ParagraphStyle(
        "Body",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=13.2,
        textColor=DARK,
        spaceAfter=6,
    ),
    "Code": ParagraphStyle(
        "Code",
        parent=SAMPLE["Code"],
        fontName="Courier",
        fontSize=8.7,
        leading=12,
        leftIndent=10,
        rightIndent=10,
        borderColor=MID,
        borderWidth=0.5,
        borderPadding=7,
        backColor=LIGHT,
        spaceAfter=7,
    ),
    "TableHeader": ParagraphStyle(
        "TableHeader",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7.7,
        leading=9.5,
        textColor=colors.white,
        alignment=TA_LEFT,
    ),
    "TableBody": ParagraphStyle(
        "TableBody",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.8,
        textColor=DARK,
        alignment=TA_LEFT,
    ),
    "CalloutTitle": ParagraphStyle(
        "CalloutTitle",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.2,
        leading=13,
        textColor=NAVY,
    ),
    "CalloutBody": ParagraphStyle(
        "CalloutBody",
        parent=SAMPLE["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12.5,
        textColor=DARK,
    ),
}


if __name__ == "__main__":
    raise SystemExit(main())
