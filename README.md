# CausalCred executable evaluation artifact

This package provides a deterministic, executable evaluation of the Causal-ABAC control flow described in **CausalCred: Post-Quantum Anonymous Provenance-Bound ABAC for AI-Agent Tool Use**. It includes concrete credential, delegation, provenance-event, challenge, proof-statement, gateway, and protected-service state for every reference trial.

The package maintains two explicit evidence classes:

1. `executed_reference_runtime` records are produced by executing the protocol state machine. They include 6,500 attack trials, seven single-control mutation experiments, reference baseline profiles, complete JSONL traces, clustered-bootstrap intervals, and sample-level runtime measurements.
2. `manuscript_summary` and `deterministic_derivation_from_manuscript_summary` records preserve manuscript tables and recompute their arithmetic. These records support transcription and consistency checks. They are not used as execution evidence.

The distinction is enforced in file paths, row-level metadata, result indexes, and verification checks.

## Quick start

Requirements are Python 3.11 or later and GNU Make. The default workflow has no third-party Python dependency.

```bash
make verify
```

Expected final output:

```text
verification: PASS
```

To collect 100 local sample-level timings after 10 warm-ups:

```bash
make benchmark
```

Container execution:

```bash
docker build -t causalcred-artifact .
docker run --rm causalcred-artifact
```

## Executed evidence

- `src/causalcred_eval/protocol.py`: concrete protocol state and verification runtime.
- `src/causalcred_eval/experiments.py`: trial generation, baselines, mutations, clustered bootstrap, provenance, and benchmarking.
- `data/executed/trials/*.jsonl`: complete trial records partitioned by testbed and attack family.
- `data/executed/protocol_trial_index.csv`: compact reviewer index for all 6,500 trials.
- `data/executed/control_ablations.jsonl`: paired full and single-control-removed executions.
- `data/executed/baseline_trials.jsonl`: executions under six registered control profiles.
- `results/executed/reference_metrics.json`: independently computed reference outcomes and intervals.
- `results/benchmarks/`: sample-level reference-runtime measurements and environment metadata.
- `environment/execution_provenance.json`: model identifier, decoding configuration, source digest, configuration, and runtime environment.

## Manuscript consistency evidence

- `data/reported/`: manuscript summary inputs.
- `data/manuscript_derived/`: deterministic derivations from those summary inputs.
- `results/tables/table01.*` through `table13.*`: CSV, Markdown, and LaTeX table forms.
- `results/metrics.json`: recomputed manuscript arithmetic and evidence-boundary metadata.
- `RESULTS_INDEX.md`: claim-to-source and claim-to-output mapping.

## Protocol-runtime scope

The reference runtime validates compound-principal binding, delegation attenuation, provenance-parent completeness, conservative integrity propagation, endorsements, nonce consumption, current epochs and revocation, exact-request binding, and suite binding. Domain-separated SHA-256 commitments provide stable state and statement identifiers.

The runtime is an executable protocol specification. Its timings do not estimate Ligetron, ML-DSA, ML-KEM, TPM, TEE, or production service performance. Cryptographic security follows the formal assumptions in the manuscript and must be evaluated against the concrete cryptographic implementation used for deployment.

## Determinism and provenance

The executed experiments use the registered local model identifier `deterministic-policy-agent-v1`, temperature 0, disabled sampling, and the seed in `configs/evaluation.json`. No network service, model API, or system clock participates in `make reproduce`. All source inputs receive SHA-256 digests. `MANIFEST.sha256` covers the release contents.

See `ARTIFACT.md` for the reviewer procedure, evidence schema, expected invariants, and interpretation rules.

## License

Evaluation code and structured data are provided under the MIT License. The manuscript retains its stated publication terms.
