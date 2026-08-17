# CausalCred artifact evaluation guide

## 1. Evaluation objective

The artifact enables reviewers to inspect and execute the protocol-level controls that bind compound identity, delegation, provenance, state freshness, revocation, request integrity, and cryptographic-suite selection. It also regenerates manuscript tables while preserving a machine-readable distinction between executed evidence and manuscript-summary arithmetic.

## 2. Reviewer workflow

Run the following command from the package root:

```bash
make verify
```

The command performs these steps:

1. executes 6,500 complete reference-runtime attack trials
2. executes 3,500 paired single-control mutation trials
3. executes every trial under six baseline control profiles
4. computes Wilson and template-clustered bootstrap intervals
5. regenerates the manuscript-derived tables and metrics
6. runs the unit, integration, mutation, and statistical tests
7. validates 114 registered invariants and writes the release manifest

The final line must be `verification: PASS`.

## 3. Evidence classes

| Evidence class | Meaning | Primary location |
| --- | --- | --- |
| `executed_reference_runtime` | Produced by executing concrete protocol state and verifier logic | `data/executed/` |
| `measured_reference_runtime` | Sample-level timing collected from the local executable specification | `results/benchmarks/` |
| `manuscript_summary` | Value transcribed from the manuscript | `data/reported/` |
| `deterministic_derivation_from_manuscript_summary` | Arithmetic or row projection derived from a manuscript summary | `data/manuscript_derived/` |

An evidence class must not be interpreted outside its stated scope.

## 4. Executed claims

| ID | Claim | Evidence | Verification condition |
| --- | --- | --- | --- |
| E1 | The complete reference relation blocks A1-A13 in both testbeds | `trials/*.jsonl` | 0 effects in 6,500 trials |
| E2 | Every C1-C7 control changes an attack outcome | `control_ablations.jsonl` | full relation rejects and paired removal permits |
| E3 | Reduced control profiles expose protected effects | `baseline_trials.jsonl` | complete profile has zero effects and weaker profiles have nonzero effects |
| E4 | Request substitution is detected after proof construction | A10 traces and runtime tests | valid reference proof followed by gateway rejection |
| E5 | Provenance omission is detected before proof construction | A5 traces and runtime tests | monitor rejection and no proof |
| E6 | Trial allocation and source identity are immutable | trial index and provenance record | 26 cells of 250 trials and valid SHA-256 digests |

## 5. Evidence inspection

The compact trial index contains one row per execution. A complete JSONL record additionally contains the challenge, credential roots, delegation, event graph, proven request, forwarded request, state digest, statement digest, stage decisions, and rejection reason.

Reviewer-oriented metrics are in `results/executed/reference_metrics.json`. Manuscript-derived metrics remain in `results/metrics.json` and identify their evidence boundary explicitly.

## 6. Mutation checks

The test suite verifies all registered attacks using concrete protocol state. It also constructs a dedicated mutation for each control, removes only that control, and requires the protected-effect decision to change. These checks prevent a verifier that merely compares an attack identifier with an expected outcome.

## 7. Reproducibility parameters

- Provider: `local-deterministic`
- Model: `deterministic-policy-agent-v1`
- Sampling: disabled
- Temperature: 0
- Top-p: 1
- Trial seed: `causalcred-reference-execution-v1`
- Bootstrap iterations: 2,000
- Trial count: 250 per attack family per testbed

All parameters are stored in `configs/evaluation.json` and copied into the execution provenance record.

## 8. Performance interpretation

The provided benchmark samples characterize the Python reference runtime. They validate sample retention, warm-up policy, timing collection, and environment recording. They do not estimate concrete post-quantum proof generation, verification, attestation, or network cost.

## 9. Clean-room reproduction

For a clean rerun:

```bash
make clean
make verify
```

Generated JSON, JSONL, CSV, Markdown, and LaTeX outputs are recreated from source and configuration. Sample-level benchmark data are retained as measurement evidence. Run `make benchmark` to collect a new local timing set.

## 10. Integrity

Run:

```bash
sha256sum -c MANIFEST.sha256
```

Every listed file must report `OK`. The manuscript digest is also validated by the verification program.
