# Regenerated manuscript tables

# Table 1: Positioning against the closest top-tier approaches

| Approach | Hidden identity | Delegation | Stateful policy | Influence integrity | Exact-action binding | Remote ZK proof | PQ transcript privacy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Conventional ABAC / Linux ABAC [21] | ✗ | △ | △ | ✗ | △ | ✗ | ✗ |
| StatefulAuth [1] | ✗ | △ | ✓ | ✗ | ✓ | ✗ | ✗ |
| Anonymous credentials [3, 15, 16] | ✓ | △ | △ | ✗ | △ | △ | ✗ |
| FDAAC-CR [25] | ✓ | ✓ | △ | ✗ | △ | △ | ✗ |
| ACE [9] | ✗ | △ | ✓ | ✓ | ✓ | ✗ | ✗ |
| AttriGuard [7] | ✗ | ✗ | ✗ | ✓ | △ | ✗ | ✗ |
| SAGA [18] | ✗ | ✓ | ✓ | △ | ✓ | ✗ | ✗ |
| CausalCred | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

# Table 2: Core notation

| Notation | Meaning |
| --- | --- |
| z_X, C_X, A_X | hidden root, root commitment, attribute root for X |
| D, τ, P | delegation chain, task contract, Causal-ABAC policy |
| E_n, G_n, S_n | event prefix, influence DAG, compact policy state |
| mh_n, σ_n^R | nonce-fresh monitor head and monitor signature |
| q = (op, res, args) | exact protected request |
| L_{P,c} | policy- and context-dependent leakage function |
| t_Y, K_Y | authority threshold and accepted key set for class Y |

# Table 3: Concrete CausalCred-PQ profile

| Function | Instantiation |
| --- | --- |
| Issuer, attester, monitor, root signatures | ML-DSA-65 |
| Authority collusion resistance | independent t_Y-of-n_Y ML-DSA signatures |
| Task channel / optional capability key | ML-KEM-768 + KMAC256 KDF |
| Commitments and event chain | SHAKE256 with 384-bit output, domain-separated |
| Attributes and revocation | SHAKE256/384 Merkle / sparse-Merkle trees |
| Scoped pseudonym | T_c = KMAC256_zα("nym" \|\| c) |
| Proof system | Ligetron transparent post-quantum ZK-SNARK |
| Symmetric action authentication | KMAC256, optional profile only |

# Table 4: Cloud-testbed uncontrolled-effect rate (UER), Wilson 95% intervals

| ID | Baseline | G1 (n=1,500) | G2 (n=750) | G3 (n=1,000) | In-scope aggregate |
| --- | --- | --- | --- | --- | --- |
| B0 | Workload identity + ABAC [21] | 1184/1500; 78.93 [76.80, 80.92] | n/a | 712/1000; 71.20 [68.32, 73.92] | 1896/2500; 75.84 [74.12, 77.48] |
| B1 | StatefulAuth [1] | n/a | n/a | 124/1000; 12.40 [10.50, 14.59] | 124/1000; 12.40 [10.50, 14.59] |
| B2 | Anonymous credentials [16] | n/a | 215/750; 28.67 [25.55, 32.01] | 668/1000; 66.80 [63.82, 69.65] | 883/1750; 50.46 [48.12, 52.80] |
| B3 | SAGA [18] | 543/1500; 36.20 [33.81, 38.66] | 161/750; 21.47 [18.68, 24.55] | 186/1000; 18.60 [16.31, 21.13] | 890/3250; 27.38 [25.88, 28.94] |
| B4 | ACE [9] | n.m. | n/a | n/a | n.m. |
| B5 | Signed plaintext trace | 672/1500; 44.80 [42.30, 47.33] | n/a | 403/1000; 40.30 [37.30, 43.37] | 1075/2500; 43.00 [41.07, 44.95] |
| B6 | CausalCred | 0/1500; 0.00 [0.00, 0.26] | 0/750; 0.00 [0.00, 0.51] | 0/1000; 0.00 [0.00, 0.38] | 0/3250; 0.00 [0.00, 0.12] |

# Table 5: Per-operation cost, median [interquartile range] over 100 runs

| Operation | Cost | Peak RSS | Status |
| --- | --- | --- | --- |
| Issue, t_I = 1 | 4.6 [4.4-4.9] ms | 21 MiB | reported_summary |
| Issue, t_I = 3 | 12.1 [11.7-12.8] ms | 26 MiB | reported_summary |
| Attest, t_T = 1 | 5.2 [5.0-5.5] ms | 24 MiB | reported_summary |
| Delegate (one edge) | 1.4 [1.3-1.5] ms | 12 MiB | reported_summary |
| Observe (one event) | 0.42 [0.40-0.45] ms | 38 MiB | reported_summary |
| Head | 0.61 [0.59-0.65] ms | 38 MiB | reported_summary |
| Prove | 8.42 [8.19-8.71] s | 412 MiB | reported_summary |
| Verify | 0.38 [0.37-0.40] s | 96 MiB | reported_summary |
| Revoke (epoch update) | 63 [61-67] ms | 44 MiB | reported_summary |
| Proof size \|π\| | 4.83 MiB |  | reported_summary |
| Statement size \|x\| | 1184 B |  | reported_summary |
| End-to-end action latency | 9.65 s |  | reported_summary |
| Capability profile, b = 16 (amortised) | 0.92 s |  | reported_summary |

# Table 6: Profile comparison at 137 Ligetron repetitions

| Profile | N (M) | Prove (s) | Verify (s) | \|π\| (MiB) | Status |
| --- | --- | --- | --- | --- | --- |
| Ed25519 | 143.1 | 5.78 | n.m. | 4.00 | reported_summary |
| ML-DSA-65 | 208.3 | 8.42 | 0.38 | 4.83 | reported_summary |
| Hybrid | 273.5 | 11.06 | n.m. | 5.54 | reported_summary |

# Table 7: Software-supply-chain attack results

| Mechanism | Trial set | Observed/trials | Rate [95% CI] (%) |
| --- | --- | --- | --- |
| CausalCred | G1 (A1-A6) | 0/1500 | 0.00 [0.00, 0.26] |
| CausalCred | G2 (A7-A9) | 0/750 | 0.00 [0.00, 0.51] |
| CausalCred | G3 (A10-A13) | 0/1000 | 0.00 [0.00, 0.38] |
| CausalCred | All A1-A13 | 0/3250 | 0.00 [0.00, 0.12] |
| Speranza-style | Digest subset* | 241/250 | 96.40 [93.30, 98.09] |
| CausalCred | Same subset | 0/250 | 0.00 [0.00, 1.51] |

# Table 8: Cloud-testbed single-control ablations (3,250 trials each)

| ID | Removed mechanism | Success/trials | UER [95% CI] (%) |
| --- | --- | --- | --- |
| C0 | None, full CausalCred | 0/3250 | 0.00 [0.00, 0.12] |
| C1 | Root binding, P_root (M2) | 391/3250 | 12.03 [10.96, 13.19] |
| C2 | Nonce-fresh head (M1) | 320/3250 | 9.85 [8.87, 10.92] |
| C3 | Integrity propagation (M3) | 734/3250 | 22.58 [21.18, 24.05] |
| C4 | Endorsement checking (M4) | 159/3250 | 4.89 [4.20, 5.69] |
| C5 | Exact-action binding, H(q) in x | 349/3250 | 10.74 [9.72, 11.85] |
| C6 | Current revocation, RevOK | 270/3250 | 8.31 [7.41, 9.31] |
| C7 | Suite binding, suiteID | 189/3250 | 5.82 [5.06, 6.67] |

# Table 9: Conditional guarantees under compromise and collusion in proof-per-action mode

| Compromise / collusion | Preserved | No longer guaranteed |
| --- | --- | --- |
| LLM, planner, or prover | proof soundness; identity privacy; exact-action verification | task correctness and utility |
| External source, tool, or subagent | gateway-enforced integrity policy | factual correctness of that source |
| Colluding holders / delegates | non-amalgamation and scope intersection | properties explicitly permitting collective witnesses |
| Verifiers + honest-issuance logs | presentation anonymity and cross-context unlinkability under Equation (13) | network, action, timing, and policy-set anonymity |
| Fewer than t_Y authorities | quorum authenticity and collusion resistance | availability if honest members refuse service |
| At or above the threshold in one authority class | past ZK transcript privacy | future authenticity for that class (credentials, attestations, or roots) |
| Monitor R corrupted before the challenged head | credential soundness and witness privacy | influence completeness, label integrity, monitor non-frameability |
| Gateway G corrupted | cryptographic transcript validity and privacy | enforcement of the protected effect; MAC-profile non-frameability |
| Current holder roots compromised | other principals' security; past untagged ZK privacy | future authentication; tagged-history unlinkability; delegation-key security |
| Later break of classical branch | fully PQ public-transcript guarantees | classical-only profile and any public classical identifier |

# Table 10: Reported AI-agent and trial configuration

| Item | Executed value | Status |
| --- | --- | --- |
| Model configuration | One immutable snapshot and fixed decoding parameters across both testbeds | identifier unavailable |
| Implementation | One immutable commit; development runs excluded | commit identifier unavailable |
| Attack allocation | 13 families; 250 trials per family and testbed | reported and checked |
| Per-testbed groups | G1: 1,500; G2: 750; G3: 1,000 | reported and checked |
| Trial totals | 3,250 per testbed; 6,500 overall | reported and checked |
| Correction control | Full 6,500-trial suite rerun after the A5 correction | reported and modeled |
| Microbenchmarks | 10 warm-ups and 100 measured runs | summary observations only |

# Table 11: Compiled WASM instruction count and evaluated bound terms

| Category | Component or term | Value | Share or bound | Status |
| --- | --- | --- | --- | --- |
| Instructions | N_cred (3 credentials) | 55.2 M | 26.5% | reported_summary |
| Instructions | N_del (2 edges) | 29.4 M | 14.1% | reported_summary |
| Instructions | N_att (1 attestation) | 19.1 M | 9.2% | reported_summary |
| Instructions | N_state (openings, transitions, receipts) | 62.8 M | 30.1% | reported_summary |
| Instructions | N_P (16 policy clauses) | 24.3 M | 11.7% | reported_summary |
| Instructions | N_rev (6 non-membership paths) | 17.5 M | 8.4% | reported_summary |
| Instructions | N_total | 208.3 M | 100% | computed_sum |
| Bound | ZK extraction | Adv_ZK^se-ks | <= 2^-96 | computed |
| Bound | ML-DSA, N_sigma = 12 | N_sigma Adv_MLDSA^euf-q | <= 2^-124.4 | computed |
| Bound | Commitments, N_C = 14 | N_C Adv_Com^qbind | <= 2^-188.2 | computed |
| Bound | Hashes, N_H = 96 | N_H Adv_H^qcoll | <= 2^-185.4 | computed |

# Table 12: Scaling from the base configuration

| Configuration | N (M) | Prove (s) | \|π\| (MiB) | Verify (s) | Status |
| --- | --- | --- | --- | --- | --- |
| n_c = 1 | 171.5 | 6.93 | 4.39 | 0.35 | reported_summary |
| n_c = 2 | 189.9 | 7.68 | 4.61 | 0.36 | reported_summary |
| n_c = 3 (base) | 208.3 | 8.42 | 4.83 | 0.38 | reported_summary |
| n_c = 4 | 226.7 | 9.16 | 5.04 | 0.39 | reported_summary |
| n_c = 8 | 300.3 | 12.14 | 5.79 | 0.44 | reported_summary |
| d = 1 | 193.6 | 7.83 | 4.66 | 0.36 | reported_summary |
| d = 4 | 237.7 | 9.61 | 5.16 | 0.40 | reported_summary |
| d = 8 | 296.5 | 11.98 | 5.76 | 0.44 | reported_summary |
| n_p = 8 | 196.2 | 7.93 | 4.69 | 0.37 | reported_summary |
| n_p = 32 | 232.6 | 9.40 | 5.11 | 0.39 | reported_summary |
| n_p = 64 | 281.2 | 11.36 | 5.61 | 0.43 | reported_summary |
| n_e = 10 | 170.5 | 6.89 | 4.37 | 0.35 | reported_summary |
| n_e = 10^3 | 586.3 | 23.70 | 8.11 | 0.59 | reported_summary |
| n_e = 10^4 | 4366.3 | 176.5 | 22.13 | 1.44 | reported_summary |
| n_e = 10^4, compaction at 256 | 273.8 | 11.07 | 5.54 | 0.42 | reported_summary |

# Table 13: Pre-registered mapping of attack families to security properties

| Group | ID | Attack family | Manipulated invariant | Formal security property | Rejecting relation component |
| --- | --- | --- | --- | --- | --- |
| G1 | A1 | Direct prompt injection | An attacker-controlled prompt determines a protected request field. | Provenance-integrity non-laundering, Definition 8 and Theorem 5. | Safe_P, Equations (8) and (11). |
| G1 | A2 | Indirect retrieval injection | Retrieved attacker-controlled content determines a protected field. | Provenance-integrity non-laundering, Definition 8 and Theorem 5. | Safe_P, Equations (8) and (11). |
| G1 | A3 | Malicious tool output | A low-integrity tool result is propagated into a protected field. | Provenance-integrity non-laundering, Definition 8 and Theorem 5. | Safe_P, Equations (8) and (11). |
| G1 | A4 | Compromised subagent | An untrusted subagent contribution is treated as an authorised source; a foreign certified root may also be introduced. | Provenance-integrity non-laundering, Definition 8 and Theorem 5; non-amalgamation where a foreign root is used. | Safe_P and, where applicable, PrincipalOK. |
| G1 | A5 | Provenance omission | A required input, transformation, parent edge, or executed-effect receipt is removed from the proved prefix. | Influence completeness and provenance-integrity non-laundering, Definitions 7-8 and Theorem 5. | OpenState, TransitionsOK, and ReceiptChainOK. |
| G1 | A6 | Event reordering | Delivered events are reordered while retaining their individual values. | Influence completeness, Definition 7 and Theorem 5. | OpenState, TransitionsOK, and Equation (15). |
| G2 | A7 | Credential amalgamation | Credentials from unrelated hidden roots are combined into one witness. | Compound-principal non-amalgamation, Definition 4 and Theorem 4. | PrincipalOK and P_root in Equation (12). |
| G2 | A8 | False two-agent independence | Two approval roots are submitted as independent. Common-controller rejection additionally assumes issuer-certified one-controller-to-one-root semantics. | Cryptographic root distinctness under Definition 4 and Theorem 4; controller independence is conditional on issuance semantics. | The distinct-root predicate in P_root and, for controller independence, the issuer uniqueness relation. |
| G2 | A9 | Delegation widening | A child delegation enlarges scope, purpose, depth, expiry, or the permitted action set. | Delegation integrity, Definition 5 and Theorem 4. | DelegationOK, attenuation in Equation (5), and action intersection in Equation (6). |
| G3 | A10 | Request substitution | The gateway receives q' != q after the proof or monitor head was constructed for q. | Exact-action binding, the binding experiment in Section 7.3 and Equation (26). | Bind and H(q) in Equations (17)-(18). |
| G3 | A11 | Replay | A previously accepted nonce, monitor head, proof, or task/context binding is submitted again. | Replay resistance and nonce freshness, the replay experiment in Section 7.3 and Equation (26). | Bind, Unused(nu), Equation (17), and atomic nonce consumption in Algorithm 1. |
| G3 | A12 | Stale attestation or revocation | The witness uses an expired or revoked handle, or a root bundle outside the permitted staleness window. | Revocation and freshness, Definition 6 and Theorem 4. | RootBundleOK, RevOK, and P_fresh in Equations (12) and (18). |
| G3 | A13 | Suite downgrade | A proof, credential, root bundle, capability, or task transcript is rebound to a weaker cryptographic suite. | Post-quantum suite binding under Theorems 3 and 7. | Bind, suiteID, and the transcript hash in Equations (17), (18), and (24). |
