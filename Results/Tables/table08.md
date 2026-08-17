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
