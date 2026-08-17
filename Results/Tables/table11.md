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
