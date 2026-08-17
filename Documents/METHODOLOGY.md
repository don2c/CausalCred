# Evaluation methodology

## Evidence separation

Executed evidence and manuscript-derived evidence are stored separately. Every record carries an `evidence_class` field. Verification rejects an executed-evidence set with an unexpected class, allocation, digest format, or outcome count.

## Executed protocol stages

Each reference trial constructs and records:

1. compound sponsor, workload, agent, and approval roots
2. credentials and an attenuating delegation edge
3. monitor events with indices, parents, declared context, integrity labels, and endorsements
4. a nonce-bearing challenge with policy, revocation, attestation, and suite epochs
5. a proof-bound request and the request forwarded to the gateway
6. monitor, relation, proof, gateway, and protected-effect decisions

An attack succeeds only when the protected service executes the generated attacker goal. A selected goal, monitor record, proof construction, or gateway rejection does not count as an effect.

## Attack execution

Every A1-A13 generator mutates concrete state. Examples include an omitted model-context parent, a future event parent, a foreign compound-principal root, a widened delegation operation, a previously consumed nonce, a stale revocation epoch, a post-proof request substitution, and a downgraded suite identifier.

The full relation evaluates 250 trials for each attack family in each of two testbeds. G1 goal selection is generated from a registered hash threshold. G2 and G3 mutations are always attempted. Complete trial traces are written before summary computation.

## Control mutation analysis

The C1-C7 experiment creates one state that violates only the selected control. Each scenario is executed twice using identical inputs. The first execution uses all controls. The second removes exactly one control. Verification requires zero protected effects under the complete relation and an effect in every paired removed-control execution.

## Reference baselines

Six control profiles are registered in code. Every profile receives the same scenario object and attacker-goal predicate. Baseline results are derived by executing the same verifier with the profile's control set. They are independent of the manuscript-summary baseline counts.

## Statistical procedures

- UER confidence intervals use the two-sided Wilson score interval with `z = 1.96`.
- Template-clustered intervals resample complete template clusters with replacement for 2,000 deterministic iterations.
- Metadata-linkage AUC uses the Mann-Whitney interpretation with half credit for tied positive-negative scores.
- Padding overhead uses the arithmetic mean of `(padded_size / original_size) - 1`.
- Security terms use multiplicity-weighted union bounds.

The cluster-bootstrap implementation is tested for deterministic output and preservation of cluster structure.

## Runtime measurements

`make benchmark` performs 10 warm-ups and records 100 individual `perf_counter_ns` measurements for the reference authorisation runtime. The CSV contains each sample and its environment. These measurements characterize the executable specification only.

## Source identity

`environment/execution_provenance.json` records a SHA-256 digest over the source, tests, configurations, scripts, documentation, and build files that define the evaluation. The release manifest hashes every distributed file except the manifest itself.
